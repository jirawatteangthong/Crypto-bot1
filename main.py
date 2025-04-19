from flask import Flask
import threading
import requests
import time
import os
import hmac
import hashlib
import json

# === ตั้งค่า BOT ===
API_KEY = 'EmgLSyDgCyWym11Xcjq8tLeDaWuszl8n3PsOw9SYypVqlCHulrKxvRxNctCq121X'
API_SECRET = '2jqYRrjyO8RTOOHT5yKNdtHuFNmS0OcRmOrB7Tj9wDnRaTjwspCxfkPxqJUL3GOJ'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
symbol = 'BTCUSDT'
leverage = 15
base_url = 'https://fapi.binance.com'
headers = {'X-MBX-APIKEY': API_KEY}

app = Flask(__name__)

# === แจ้งเตือน Telegram ===
def notify_telegram(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    try:
        requests.post(url, data=data)
    except:
        pass

# === ดึงราคาปัจจุบัน ===
def get_price(symbol):
    url = f"{base_url}/fapi/v1/ticker/price?symbol={symbol}"
    try:
        res = requests.get(url)
        return float(res.json()['price'])
    except:
        notify_telegram("ERROR: ไม่สามารถดึงราคาได้")
        return None

# === ฟังก์ชันเปิดออเดอร์ Futures ===
def open_futures_order(symbol, side, quantity, entry_price, sl_price, tp_price):
    timestamp = int(time.time() * 1000)
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': quantity,
        'price': str(entry_price),
        'timestamp': timestamp
    }

    query = '&'.join([f"{key}={params[key]}" for key in params])
    signature = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature

    url = f"{base_url}/fapi/v1/order"
    try:
        res = requests.post(url, headers=headers, data=params)
        notify_telegram(f"เปิดออเดอร์ {side} ที่ราคา {entry_price}\nTP: {tp_price}\nSL: {sl_price}")
        return res.json()
    except Exception as e:
        notify_telegram(f"ERROR เปิดออเดอร์: {e}")
        return None

# === กลยุทธ์เริ่มต้น (ตัวอย่าง) ===
def strategy_bot():
    while True:
        price = get_price(symbol)
        if price is None:
            time.sleep(10)
            continue

        balance = 100  # สมมุติทุน $100
        entry_price = round(price, 2)
        position_size = round((balance * 0.3 * leverage) / price, 3)

        tp_price = round(entry_price * 1.3, 2)   # +30%
        sl_price = round(entry_price * 0.88, 2)  # -12%

        side = 'BUY'  # ตัวอย่างขา BUY (คุณสามารถเขียน logic OB + FVG + CHoCH มาเพิ่มเอง)

        open_futures_order(symbol, side, position_size, entry_price, sl_price, tp_price)
        notify_telegram(f"เทรดตัวอย่างแล้ว! (จำลอง) : {side} {position_size} @ {entry_price}")
        time.sleep(300)  # เทรดทุก 5 นาที (เพื่อทดสอบ)

# === HOME PAGE ของ BOT ===
@app.route('/')
def home():
    return "Crypto Bot is running!"

# === เริ่มบอท ===
if __name__ == '__main__':
    notify_telegram("✅ Bot Started on Render!")
    bot_thread = threading.Thread(target=strategy_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
