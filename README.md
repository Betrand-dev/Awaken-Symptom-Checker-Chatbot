## Introduction
``Awaken`` is a simple Ai powered chatbot the use ``openai api key `` to allow user to
enter thier symptoms and it replies them with possible causes , possible diseases and ways to 
solve thier problems.
# **Get Started**
Awaken is a flask web app made with HTML, CSS and JAVASCRIPT.
to get started first clone the repo
```bash
git clone https://github.com/Betrand-dev/Awaken-Symptom-Checker-Chatbot.git
```
then enter directory
```bash
cd Awaken-Symptom-Checker-Chatbot
```
then install dependencies 
```bash
pip install Flask requests openai python-dotenv langdetect googletrans mysql-connector-python 
```
``Note`` : this project uses mysql-connector-python to connect to Xamp MySQL databse so you must have xamp install and start ``apache`` and ``mysql``
# **Setting up project**
[1] Get an api an api api key from ``openai``
[2] Start xamp and open you broswer and create a database called ``awaken_db``
Next you need to create a file in the root directory and called it ``.env``
