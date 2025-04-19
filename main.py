from flask import Flask
import threading
import time
import requests
import os

# ==== CONFIG ====
API_KEY = 'EmgLSyDgCyWym11Xcjq8tLeDaWuszl8n3PsOw9SYypVqlCHulrKxvRxNctCq121X'
API_SECRET = '2jqYRrjyO8RTOOHT5yKNdtHuFNmS0OcRmOrB7Tj9wDnRaTjwspCxfkPxqJUL3GOJ'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

symbol = 'BTCUSDT'
base_url = 'https://fapi.binance.com'

headers = {
    'X-MBX-APIKEY': API_KEY
}

app = Flask(__name__)

# ==== ส่งข้อความ Telegram ====
def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# ==== ดึงราคาจาก Binance (พร้อมกันบั๊ก 'price') ====
def get_price():
    try:
        url = f"{base_url}/fapi/v1/ticker/price?symbol={symbol}"
        res = requests.get(url)
        data = res.json()
        if 'price' in data:
            return float(data['price'])
        else:
            notify_telegram(f"ERROR: ไม่พบราคาจาก Binance\n{data}")
            return None
    except Exception as e:
        notify_telegram(f"ERROR: {str(e)}")
        return None

# ==== ฟังก์ชันวิเคราะห์และเทรด ====
def run_bot():
    notify_telegram("Bot Started! เริ่มทำงานแล้ว")
    while True:
        price = get_price()
        if price:
            print(f"[ราคา BTCUSDT] {price}")
            # ----- ตรงนี้ใส่กลยุทธ์ OB, FVG, Fibonacci, CHoCH ได้เลย -----

        time.sleep(60)  # ดึงราคาทุก 60 วินาที

# ==== หน้าเว็บหลักสำหรับ Render ====
@app.route('/')
def home():
    return 'Crypto Bot is running!'

# ==== เริ่ม Flask + Background Bot ====
if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
