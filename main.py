from flask import Flask
import requests
import time

app = Flask(__name__)

# ========== ตั้งค่าพื้นฐาน ==========

API_KEY = 'EmgLSyDgCyWym11Xcjq8tLeDaWuszl8n3PsOw9SYypVqlCHulrKxvRxNctCq121X'
API_SECRET = '2jqYRrjyO8RTOOHT5yKNdtHuFNmS0OcRmOrB7Tj9wDnRaTjwspCxfkPxqJUL3GOJ'
TELEGRAM_TOKEN = '7953637965:AAHqv_avrTlv3SCDx34e1NiadajuZDJkbDU'
TELEGRAM_CHAT_ID = '8104629569'

symbol = 'BTCUSDT'
leverage = 15
base_url = 'https://fapi.binance.com'

headers = {
    'X-MBX-APIKEY': API_KEY
}


# ========== ฟังก์ชันสำหรับการแจ้งเตือน Telegram ==========
def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except:
        pass


# ========== ตัวอย่างโค้ดหลัก (รอคุณเพิ่ม logic OB, FVG, Fib) ==========
@app.route('/')
def run_bot():
    notify_telegram("Bot Started! รันสำเร็จแล้ว!")

    # คุณสามารถเพิ่ม logic วิเคราะห์ M15 และ M5 ตรงนี้
    # เช่น ดึงแท่งเทียน M15
    # วิเคราะห์ Order Block, Fair Value Gap, Fibonacci
    # จากนั้นถ้าพบจุดเข้า ส่งออเดอร์ไปที่ Binance

    return 'Crypto Bot is Running!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
