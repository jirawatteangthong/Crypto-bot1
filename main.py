from flask import Flask
import threading
import time
import requests
import os

app = Flask(__name__)

# === ตั้งค่า Telegram ===
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

# === ตั้งค่า Binance Futures ===
SYMBOL = "BTCUSDT"
BINANCE_FUTURES_URL = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}"

# === ฟังก์ชันส่งแจ้งเตือน Telegram ===
def notify_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, data=payload)
        if not response.ok:
            print("[Telegram Error]", response.text)
    except Exception as e:
        print(f"[ERROR] แจ้งเตือนไม่สำเร็จ: {e}")

# === ฟังก์ชันดึงราคาจาก Binance ===
def get_price():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(BINANCE_FUTURES_URL, headers=headers, timeout=10)
        data = response.json()

        print(f"[DEBUG] Binance Response: {data}")

        if 'price' in data:
            return float(data['price'])
        else:
            notify_telegram(f"[ERROR] ไม่พบข้อมูลราคา: {data}")
            return None
    except Exception as e:
        notify_telegram(f"[ERROR] ดึงราคาไม่สำเร็จ: {e}")
        return None

# === ฟังก์ชันรันบอท ===
def run_bot():
    notify_telegram("บอทเริ่มทำงานแล้ว!")

    while True:
        price = get_price()
        if price:
            print(f"[INFO] BTCUSDT = {price}")
        else:
            print("[ERROR] ไม่สามารถดึงราคา BTCUSDT ได้")

        time.sleep(30)

# === Web Route ===
@app.route('/')
def home():
    return "Crypto Bot is running!"

# === เริ่ม Flask และ Thread Background ===
if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
