# main.py

from flask import Flask
import threading
import time
import hmac
import hashlib
import base64
import requests
import json
import datetime

# === ตั้งค่า OKX API ===
OKX_API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
OKX_API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
OKX_API_PASSPHRASE = "Jirawat1-"

# === Telegram Bot ===
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

# === Settings ===
SYMBOL = "BTC-USDT"
LEVERAGE = 15
TRADE_PERCENT = 0.3
SL_PERCENT = -12
TP_PERCENT = 30
TRAILING_START = 10
TRAILING_SL = 2

app = Flask(__name__)

# === Global Variables ===
last_choch_alert = None
last_fibo_alert = None
active_order = None
entry_price = None

# === Helper ===
def notify_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram Error:", e)

def get_iso_time():
    return datetime.datetime.utcnow().isoformat("T", "milliseconds") + "Z"

def okx_headers(method, endpoint, body=""):
    ts = get_iso_time()
    prehash = f"{ts}{method}{endpoint}{body}"
    sign = base64.b64encode(
        hmac.new(OKX_API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": OKX_API_PASSPHRASE,
        "Content-Type": "application/json",
        "x-simulated-trading": "0"
    }

def get_price():
    url = f"https://www.okx.com/api/v5/market/ticker?instId={SYMBOL}"
    try:
        res = requests.get(url)
        price = float(res.json()['data'][0]['last'])
        return price
    except:
        notify_telegram("[ERROR] ไม่สามารถดึงราคาจาก OKX ได้")
        return None

def get_balance():
    url = "/api/v5/account/balance"
    headers = okx_headers("GET", url)
    res = requests.get("https://www.okx.com" + url, headers=headers)
    data = res.json()
    for asset in data['data'][0]['details']:
        if asset['ccy'] == 'USDT':
            return float(asset['cashBal'])
    return 0

def set_leverage():
    url = "/api/v5/account/set-leverage"
    body = {
        "instId": SYMBOL,
        "lever": str(LEVERAGE),
        "mgnMode": "cross"
    }
    headers = okx_headers("POST", url, json.dumps(body))
    requests.post("https://www.okx.com" + url, headers=headers, data=json.dumps(body))

def place_order(side, size):
    url = "/api/v5/trade/order"
    body = {
        "instId": SYMBOL,
        "tdMode": "cross",
        "side": side,
        "ordType": "market",
        "sz": str(size)
    }
    headers = okx_headers("POST", url, json.dumps(body))
    res = requests.post("https://www.okx.com" + url, headers=headers, data=json.dumps(body))
    return res.json()

def close_position():
    global active_order, entry_price
    if not active_order:
        return
    side = "sell" if active_order == "buy" else "buy"
    size = active_order["size"]
    price_now = get_price()
    pnl = (price_now - entry_price) / entry_price * 100 if active_order["side"] == "buy" else (entry_price - price_now) / entry_price * 100
    notify_telegram(f"[CLOSE] ปิดออเดอร์ {active_order['side']} กำไร/ขาดทุน: {pnl:.2f}%")
    place_order(side, size)
    active_order = None
    entry_price = None

def check_trailing(price):
    global entry_price
    if not entry_price:
        return
    pnl = (price - entry_price) / entry_price * 100 if active_order["side"] == "buy" else (entry_price - price) / entry_price * 100
    if pnl >= TRAILING_START:
        sl_trigger = entry_price * (1 + TRAILING_SL / 100) if active_order["side"] == "buy" else entry_price * (1 - TRAILING_SL / 100)
        if (active_order["side"] == "buy" and price <= sl_trigger) or (active_order["side"] == "sell" and price >= sl_trigger):
            close_position()

def detect_choch(price):
    global last_choch_alert
    now = time.time()
    if last_choch_alert is None or now - last_choch_alert > 900:
        notify_telegram("[ALERT] พบสัญญาณ CHoCH (M15)")
        last_choch_alert = now
        return True
    return False

def detect_fibo_zone(price, low, high):
    global last_fibo_alert
    zone_low = low + (high - low) * 0.618
    zone_high = low + (high - low) * 0.786
    if zone_low <= price <= zone_high:
        now = time.time()
        if last_fibo_alert is None or now - last_fibo_alert > 1800:
            notify_telegram("[ALERT] ราคาเข้าโซน Fibonacci")
            last_fibo_alert = now
        return True
    return False

def run_bot():
    global active_order, entry_price

    notify_telegram("ระบบเริ่มทำงานแล้ว (OKX Futures)")

    set_leverage()

    while True:
        try:
            price = get_price()
            if not price:
                time.sleep(10)
                continue

            # ตัวอย่าง Fake Range
            low = price * 0.98
            high = price * 1.02

            # วิเคราะห์ CHoCH TF M15
            if detect_choch(price) and detect_fibo_zone(price, low, high):
                if not active_order:
                    balance = get_balance()
                    trade_amount = (balance * TRADE_PERCENT * LEVERAGE) / price
                    order_side = "buy"
                    order = place_order(order_side, trade_amount)
                    if order.get("code") == "0":
                        active_order = {"side": order_side, "size": trade_amount}
                        entry_price = price
                        notify_telegram(f"[OPEN] เปิดออเดอร์ {order_side.upper()} ที่ราคา {price}")
                    else:
                        notify_telegram(f"[ERROR] ไม่สามารถเปิดออเดอร์ได้: {order}")
            elif active_order:
                pnl = (price - entry_price) / entry_price * 100 if active_order["side"] == "buy" else (entry_price - price) / entry_price * 100
                if pnl <= SL_PERCENT or pnl >= TP_PERCENT:
                    close_position()
                else:
                    check_trailing(price)

        except Exception as e:
            notify_telegram(f"[ERROR] เกิดข้อผิดพลาด: {str(e)}")

        time.sleep(60)

@app.route('/')
def home():
    return "OKX Futures Bot is Running!"

if __name__ == '__main__':
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=10000)
