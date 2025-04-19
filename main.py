from flask import Flask
import threading
import time
import requests

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
        print(f"[ERROR] แจ้งเตือน Telegram ไม่สำเร็จ: {e}")

def get_price(symbol, retries=3):
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Raw Response: {response.text}")

            if response.status_code != 200:
                time.sleep(1)
                continue

            data = response.json()
            price_str = data.get('price')
            if price_str:
                return float(price_str)
            else:
                notify_telegram(f"[ERROR] ไม่พบราคาจาก Binance: {data}")
                return None
        except Exception as e:
            print(f"[ERROR] Attempt {attempt+1}: {e}")
            time.sleep(1)

    notify_telegram("[ERROR] ดึงราคาไม่สำเร็จหลังจากพยายามหลายครั้ง")
    return None

# === ฟังก์ชันรันบอทเบื้องหลัง ===
def run_bot():
    notify_telegram("✅ บอทเริ่มทำงานแล้ว!")

    while True:
        price = get_price(SYMBOL)
        if price:
            print(f"[INFO] ราคาล่าสุด BTCUSDT = {price}")
            # ตรงนี้สามารถเขียน logic กลยุทธ์เทรดต่อได้
        else:
            print("[ERROR] ดึงราคาล้มเหลว")

        time.sleep(30)

# === route สำหรับ Render ===
@app.route('/')
def home():
    return "Crypto Bot is running!"

# === รัน Flask + Thread bot ===
if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    app.run(host="0.0.0.0", port=10000)
