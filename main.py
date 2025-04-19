from flask import Flask
import threading
import os
import time
import requests

app = Flask(__name__)

# ตั้งค่า Telegram Bot
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'  # ใส่ chat ID ของคุณตรงนี้

# ฟังก์ชันส่งข้อความไป Telegram
def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ตัวอย่างฟังก์ชันบอท
def run_bot():
    notify_telegram("Bot Started! บอทเริ่มทำงานแล้ว")
    while True:
        print("บอททำงานอยู่...")
        time.sleep(10)

@app.route('/')
def home():
    return "Crypto Bot is running!"

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
