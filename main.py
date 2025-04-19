from flask import Flask
import threading
import time
import requests
import os

app = Flask(__name__)

# ========== ตั้งค่า ==========

API_KEY = 'EmgLSyDgCyWym11Xcjq8tLeDaWuszl8n3PsOw9SYypVqlCHulrKxvRxNctCq121X'
API_SECRET = '2jqYRrjyO8RTOOHT5yKNdtHuFNmS0OcRmOrB7Tj9wDnRaTjwspCxfkPxqJUL3GOJ'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
SYMBOL = 'BTCUSDT'
LEVERAGE = 15

# ========== แจ้งเตือนผ่าน Telegram ==========

def notify_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ========== ฟังก์ชันดึงราคาจาก Binance Futures ==========

def get_price(symbol):
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0'  # เพิ่ม header เพื่อให้ Binance ยอมรับ
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        if 'price' in data:
            return float(data['price'])
        else:
            notify_telegram(f"[ERROR] ไม่พบ key 'price' ใน response: {data}")
            return None
    except Exception as e:
        notify_telegram(f"[ERROR] ดึงราคาล้มเหลว: {str(e)}")
        return None

# ========== ฟังก์ชันรันบอท ==========

def run_bot():
    notify_telegram("✅ Bot started and running!")
    while True:
        price = get_price(SYMBOL)
        if price:
            notify_telegram(f"ราคาล่าสุด {SYMBOL} = {price}")
        else:
            notify_telegram("❌ ไม่สามารถดึงราคาจาก Binance ได้")
        
        time.sleep(60)  # รอ 60 วินาทีต่อรอบ

# ========== Home page สำหรับ Flask ==========

@app.route('/')
def home():
    return "Crypto Bot is running!"

# ========== เริ่มต้น Flask และ Thread ของ Bot ==========

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
