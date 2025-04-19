from flask import Flask
import threading
import requests
import time
import os

app = Flask(__name__)

# ====== ตั้งค่า Bot ======
API_KEY = 'EmgLSyDgCyWym11Xcjq8tLeDaWuszl8n3PsOw9SYypVqlCHulrKxvRxNctCq121X'
API_SECRET = '2jqYRrjyO8RTOOHT5yKNdtHuFNmS0OcRmOrB7Tj9wDnRaTjwspCxfkPxqJUL3GOJ'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
symbol = 'BTCUSDT'
base_url = 'https://fapi.binance.com'

headers = {
    'X-MBX-APIKEY': API_KEY
}

# ====== แจ้งเตือน Telegram ======
def notify_telegram(message):
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)

# ====== ดึงราคาจาก Binance ======
def get_price(symbol):
    url = f"{base_url}/fapi/v1/ticker/price?symbol={symbol}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        # Debug log เผื่อ API กลับมาเป็นข้อความแทน
        if 'price' not in data:
            notify_telegram(f"[ERROR] ไม่พบราคาในข้อมูลที่ได้: {data}")
            return None

        price = float(data['price'])
        return price
    except Exception as e:
        notify_telegram(f"[ERROR] ดึงราคาไม่สำเร็จ: {str(e)}")
        return None

# ====== ฟังก์ชันหลักของ Bot ======
def run_bot():
    notify_telegram("Bot Started! รันสำเร็จแล้ว")
    while True:
        price = get_price(symbol)
        if price:
            notify_telegram(f"[ราคา BTC/USDT] = {price:.2f} USDT")
        else:
            notify_telegram("ไม่สามารถดึงราคาจาก Binance ได้")
        time.sleep(300)

# ====== หน้าเว็บหลัก สำหรับ Render ======
@app.route('/')
def home():
    return 'Crypto Bot is running!'

# ====== เริ่มรัน Flask และ Thread Bot ======
if __name__ == '__main__':
    thread = threading.Thread(target=run_bot)
    thread.start()

    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
