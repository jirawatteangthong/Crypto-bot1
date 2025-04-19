from flask import Flask
import threading
import requests
import os
import time

app = Flask(__name__)

# Telegram config
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        r = requests.post(url, data=data)
        print("Telegram response:", r.text)
    except Exception as e:
        print("Error sending Telegram:", e)

def run_bot():
    notify_telegram("Bot Started! รันสำเร็จแล้ว!")
    while True:
        print("กำลังทำงาน...")
        time.sleep(10)

@app.route('/')
def home():
    return 'Crypto Bot is running!'

if __name__ == '__main__':
    thread = threading.Thread(target=run_bot)
    thread.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
