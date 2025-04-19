from flask import Flask
import threading
import os
import time
import requests

app = Flask(__name__)

# ======= ตั้งค่าพื้นฐาน =======
TELEGRAM_TOKEN = '7953637965:AAHqv_avrTlv3SCDx34e1NiadajuZDJkbDU'
TELEGRAM_CHAT_ID = '8104629569'

# ======= ฟังก์ชันส่งข้อความไป Telegram =======
def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"ส่งข้อความ Telegram ไม่สำเร็จ: {e}")

# ======= โค้ดบอท (แก้ให้เป็นโค้ดเทรดจริงของคุณได้) =======
def run_bot():
    notify_telegram("Bot Started! บอทเริ่มทำงานแล้ว")
    while True:
        print("บอทกำลังทำงาน...")  # ตรงนี้ใส่ logic เทรดได้เลย
        # ตัวอย่าง: ดึงราคาจาก Binance, วิเคราะห์, ส่งคำสั่งเทรด
        time.sleep(10)  # รอ 10 วิ

# ======= หน้าเว็บ Flask =======
@app.route('/')
def home():
    return "Crypto Bot is running!"

# ======= เริ่มทำงาน Flask + Background Bot =======
if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 10000))  # Render ใช้ ENV PORT
    app.run(host='0.0.0.0', port=port)
