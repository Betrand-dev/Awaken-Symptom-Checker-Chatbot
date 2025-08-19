import os
from datetime import datetime
from uuid import uuid4

from flask import Flask, render_template, request, jsonify
from flask import send_from_directory  # useful if you just serve static files
from dotenv import load_dotenv
import requests
import mysql.connector
from openai import OpenAI

# Optional multilingual (safe fallbacks if not installed)
try:
    from langdetect import detect as detect_lang
except Exception:
    detect_lang = None

try:
    from googletrans import Translator
    _translator = Translator()
except Exception:
    _translator = None


# ---------------------------
# Config & App Setup
# ---------------------------
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "betrand-secret")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "awaken_db")

USE_TRANSLATION = os.getenv("USE_TRANSLATION", "0") == "1"

#openapi key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)


# connection to database
def db_connect():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def ensure_tables():
    conn = db_connect()
    cur = conn.cursor()
    # Create table for chat logs
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(64),
            user_message TEXT,
            bot_response TEXT,
            lang_code VARCHAR(8),
            created_at DATETIME
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )
    conn.commit()
    cur.close()
    conn.close()


ensure_tables()


# ---------------------------
# Translation Helpers (Optional)
# ---------------------------
def detect_language(text: str) -> str:
    if not USE_TRANSLATION or detect_lang is None:
        return "auto"
    try:
        return detect_lang(text)
    except Exception:
        return "auto"


def translate_to_english(text: str, src_lang: str) -> str:
    if not USE_TRANSLATION or _translator is None:
        return text
    try:
        if src_lang in ("auto", "en"):
            return text
        return _translator.translate(text, src=src_lang, dest="en").text
    except Exception:
        # Fallback: return original if translation fails
        return text


def translate_from_english(text: str, dest_lang: str) -> str:
    if not USE_TRANSLATION or _translator is None:
        return text
    try:
        if dest_lang in ("auto", "en"):
            return text
        return _translator.translate(text, src="en", dest=dest_lang).text
    except Exception:
        return text



# --------------------------
# OpenAi gpt
# --------------------------
def call_openai(user_message_en: str) -> str:
    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini', #or gpt-3.5-turbo if you want cheaper
            messages=[
                {
                    'role' : 'system',
                    'content' : (
                        'You are a Awaken carful health assistant for symptom checker.'
                        'Be brief, clear, and non-alarming. suggest common possibilities and simple self-care steps.'
                        'Avoid definitive diagnoses. Encourage professional care when appropriate.'
                    )
                },
                {
                    'role' : 'user',
                    'content' : user_message_en
                }
            ],
            max_tokens=200,
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f' Error contacting AI service {str(e)}'

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    """
    If you’re serving a Flask-template front end, keep this.
    Otherwise, serve your static SPA index via send_from_directory.
    """
    # return send_from_directory("static", "index.html")  # if pure static SPA
    return render_template("index.html")  # if using /templates/index.html


@app.route("/chat", methods=["POST"])
def chat():
    """
    Expects JSON: { "message": "...", "session_id": "optional", "lang": "optional" }
    Returns: { "reply": "...", "session_id": "..." }
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    session_id = (data.get("session_id") or "").strip()
    preferred_lang = (data.get("lang") or "").strip().lower()  # optional override

    if not user_message:
        return jsonify({"error": "Empty message."}), 400

    # Generate / persist a session id
    if not session_id:
        session_id = uuid4().hex[:24]

    # Language detect (optional)
    lang_code = preferred_lang or detect_language(user_message)

    # Translate to English for model (optional)
    user_message_en = translate_to_english(user_message, lang_code)

    # Get Gpt reply in English
    gpt_reply_en = call_openai(user_message_en)

    # Get Gpt reply back to user language
    final_reply =translate_from_english(gpt_reply_en, lang_code)


    # Store in DB
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chats (session_id, user_message, bot_response, lang_code, created_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (session_id, user_message, final_reply, lang_code, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        # Log error server-side in real apps. We still return the reply.
        print("DB insert error:", e)

    return jsonify({"reply": final_reply, "session_id": session_id})


@app.route("/history", methods=["GET"])
def history():
    """
    Fetch latest chat history for a session id.
    GET /history?session_id=abc123&limit=50
    """
    session_id = (request.args.get("session_id") or "").strip()
    limit = int(request.args.get("limit") or 50)
    limit = max(1, min(limit, 200))

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    try:
        conn = db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT user_message, bot_response, lang_code, created_at "
            "FROM chats WHERE session_id=%s ORDER BY id ASC LIMIT %s",
            (session_id, limit)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print("DB fetch error:", e)
        rows = []

    return jsonify({"session_id": session_id, "messages": rows})


# --------------- Run ---------------
if __name__ == "__main__":
    # Helpful during local dev
    app.run(debug=True)