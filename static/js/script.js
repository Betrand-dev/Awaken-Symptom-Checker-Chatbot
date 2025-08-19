document.addEventListener("DOMContentLoaded", () => {
  const sendBtn = document.getElementById("sendBtn");
  const userInput = document.getElementById("userInput");
  const chatbox = document.getElementById("chatbox");

  function appendMessage(message, sender) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add(sender + "-message");

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.textContent = message;

    msgDiv.appendChild(bubble);
    chatbox.appendChild(msgDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
  }

  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage(message, "user");
    userInput.value = "";

    // show typing...
    appendMessage("...", "bot");

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();

      // remove typing indicator
      chatbox.removeChild(chatbox.lastChild);

      appendMessage(data.reply, "bot");
    } catch (err) {
      console.error(err);
      appendMessage("⚠️ Error connecting to server.", "bot");
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
});