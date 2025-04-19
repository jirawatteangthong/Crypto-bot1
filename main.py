from flask import Flask
import threading
import os
import time
import requests

app = Flask(__name__)

# ====== ตั้งค่า Telegram ======
TELEGRAM_TOKEN = '7953637965:AAHqv_avrTlv3SCDx34e1NiadajuZDJkbDU'
TELEGRAM_CHAT_ID = '8104629569'

def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("ไม่สามารถส่ง Telegram ได้:", e)

# ====== โค้ดบอทหลัก (ใส่ Logic เทรดจริงได้ที่นี่) ======
def run_bot():
    notify_telegram("บอทเริ่มทำงานแล้วบน Render!")
    while True:
        print("บอททำงานอยู่...")  # ตรงนี้ใส่ logic เทรดจริง
        time.sleep(10)

# ====== Flask Routes ======
@app.route('/')
def home():
    return "Crypto Bot is running!"

# ====== เริ่มรัน Flask + Bot ======
if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))  # Render ใช้ PORT จาก env
    app.run(host='0.0.0.0', port=port)
