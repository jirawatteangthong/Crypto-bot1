from flask import Flask
import threading
import time
import requests
import os

# === ตั้งค่า Telegram ===
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

# === ตั้งค่า Binance Futures ===
SYMBOL = "BTCUSDT"

# === Flask App ===
app = Flask(__name__)

def notify_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] ไม่สามารถแจ้ง Telegram ได้: {e}")

def get_price(symbol):
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'price' in data:
            return float(data['price'])
        else:
            notify_telegram(f"[ERROR] ไม่พบ key 'price': {data}")
            return None

    except requests.exceptions.RequestException as e:
        notify_telegram(f"[ERROR] ดึงราคา Binance ล้มเหลว:\n{str(e)}")
        return None

# === ฟังก์ชันรันบอท ===
def run_bot():
    notify_telegram("บอทเริ่มทำงานแล้ว!")

    while True:
        price = get_price(SYMBOL)

        if price:
            print(f"[INFO] BTCUSDT = {price}")
            # คุณสามารถต่อยอดกลยุทธ์เทรดจริงได้ที่นี่
        else:
            print("[ERROR] ดึงราคาล้มเหลว")

        time.sleep(30)

@app.route('/')
def home():
    return "Crypto Bot is running!"

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
