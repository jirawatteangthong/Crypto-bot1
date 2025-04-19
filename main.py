from flask import Flask
import threading
import requests
import time
import hmac
import hashlib
import base64
import json
import datetime
import os

# ====== ตั้งค่า API OKX ======
API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
API_PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"

SYMBOL = "BTC-USDT"
INST_ID = "BTC-USDT-SWAP"

# ====== ตั้งค่า Telegram ======
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

# ====== Flask App ======
app = Flask(__name__)

# ====== ฟังก์ชันแจ้งเตือน Telegram ======
def notify_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")

# ====== ฟังก์ชันสร้าง Signature สำหรับ OKX ======
def get_okx_headers(method, path, body=""):
    timestamp = datetime.datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    prehash = f"{timestamp}{method}{path}{body}"
    signature = base64.b64encode(
        hmac.new(
            API_SECRET.encode(),
            prehash.encode(),
            hashlib.sha256
        ).digest()
    ).decode()
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

# ====== ฟังก์ชันดึงราคาจาก OKX ======
def get_okx_price(symbol):
    try:
        url = f"{BASE_URL}/api/v5/market/ticker?instId={symbol}"
        response = requests.get(url)
        data = response.json()
        price = float(data['data'][0]['last'])
        return price
    except Exception as e:
        notify_telegram(f"[ERROR] ดึงราคาจาก OKX ไม่สำเร็จ: {e}")
        return None

# ====== ใส่กลยุทธ์เทรดจริงตรงนี้ ======
def strategy_loop():
    notify_telegram("บอทเริ่มทำงานแล้ว! (OKX Futures)")

    while True:
        price = get_okx_price(INST_ID)
        if price:
            print(f"[INFO] ราคาปัจจุบัน BTC = {price}")
            # ====== จุดนี้ให้คุณเพิ่ม logic วิเคราะห์ CHoCH, Fibonacci, M15, M5 ======
            # เช่น ตรวจสอบสภาพตลาด, คำนวณโซน Fib 61.8–78.6, หาจุดกลับตัว CHoCH แล้วเทรด
        else:
            print("[ERROR] ไม่สามารถดึงราคาได้")

        time.sleep(30)

# ====== Route สำหรับ Render ======
@app.route('/')
def home():
    return "Crypto Bot (OKX) is running!"

# ====== Main ======
if __name__ == "__main__":
    bot_thread = threading.Thread(target=strategy_loop)
    bot_thread.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
