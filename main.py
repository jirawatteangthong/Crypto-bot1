# main.py
# เทรดตามระบบ ICT พร้อม Telegram ควบคุมบอท / แจ้งเตือนครบ

import time, requests, hmac, hashlib, base64, json, threading
from datetime import datetime
from flask import Flask, request

# --------------- CONFIG ----------------
API_KEY = "e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28"
API_SECRET = "3E0BDFF2AF2EF11217C2DCC7E88400C3"
PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 13
TRADE_PERCENTAGE = 0.3
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
CHAT_ID = "8104629569"
BOT_ACTIVE = True

# -------------- GLOBAL VARS ------------
in_position = False
entry_price = 0.0
order_id = None
stop_loss_price = 0.0
take_profit_price = 0.0
last_profit = 0.0

# -------------- UTILS ------------------
def get_server_time():
    res = requests.get(f"{BASE_URL}/api/v5/public/time")
    return str(res.json()['data'][0]['ts'])

def sign_request(timestamp, method, path, body):
    msg = f"{timestamp}{method.upper()}{path}{body}"
    mac = hmac.new(bytes(API_SECRET, 'utf-8'), bytes(msg, 'utf-8'), hashlib.sha256)
    d = mac.digest()
    return base64.b64encode(d).decode("utf-8")

def okx_request(method, path, data=None, private=False):
    timestamp = get_server_time()
    body = json.dumps(data) if data else ''
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sign_request(timestamp, method, path, body),
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    } if private else {}

    url = BASE_URL + path
    r = requests.request(method, url, headers=headers, data=body if data else None)
    try:
        res = r.json()
        if "data" not in res:
            send_telegram(f"[DEBUG] Response Error:\n{json.dumps(res, indent=2)}")
        return res
    except Exception as e:
        send_telegram(f"[ERROR] Request Failed: {e}")
        return None

def send_telegram(msg):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": msg
    })

def get_price():
    res = okx_request("GET", f"/api/v5/market/ticker?instId={SYMBOL}")
    return float(res["data"][0]["last"]) if res and "data" in res else 0.0

def get_balance():
    res = okx_request("GET", "/api/v5/account/balance", private=True)
    if res and "data" in res:
        for d in res["data"][0]["details"]:
            if d["ccy"] == "USDT":
                return float(d["availEq"])
    return 0.0

# ------------- SIGNAL -------------------
def is_swing_high(price):
    return price % 10 == 0  # จำลองจุด Swing High

def get_entry_signal():
    price = get_price()
    now = datetime.utcnow()
    if now.hour in [1, 2, 3]:
        if price < 70000:  # เงื่อนไขจำลอง
            send_telegram("เจอสัญญาณเข้าออเดอร์จาก Swing!")
            return True
    return False

# ------------- TRADE --------------------
def open_order():
    global in_position, entry_price, stop_loss_price, take_profit_price

    price = get_price()
    balance = get_balance()
    qty = round((balance * TRADE_PERCENTAGE * LEVERAGE) / price, 3)
    entry_price = price
    stop_loss_price = round(price * 0.985, 2)
    take_profit_price = round(price * 1.03, 2)

    okx_request("POST", "/api/v5/account/set-leverage", {
        "instId": SYMBOL,
        "lever": str(LEVERAGE),
        "mgnMode": "isolated"
    }, private=True)

    okx_request("POST", "/api/v5/trade/order", {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": "buy",
        "ordType": "market",
        "sz": str(qty)
    }, private=True)

    in_position = True
    send_telegram(f"เข้าออเดอร์ที่ {price}\nSL: {stop_loss_price}, TP: {take_profit_price}")

def close_position(profit=0):
    global in_position, last_profit
    in_position = False
    last_profit = profit
    send_telegram(f"ปิดออเดอร์: +{profit:.2f} USDT")

# ------------- MONITOR ------------------
def monitor_trade():
    global in_position, stop_loss_price, take_profit_price

    while True:
        if not BOT_ACTIVE:
            time.sleep(10)
            continue

        if in_position:
            price = get_price()
            if price >= take_profit_price:
                close_position(profit=(price - entry_price) * 1)
            elif price <= stop_loss_price:
                close_position(profit=(price - entry_price) * 1)
        else:
            if get_entry_signal():
                open_order()
        time.sleep(15)

# --------- TELEGRAM CONTROL ------------
app = Flask(__name__)

@app.route(f"/webhook", methods=["POST"])
def webhook():
    global BOT_ACTIVE
    data = request.get_json()
    msg = data["message"]["text"]
    if "/start" in msg:
        send_telegram("บอททำงานอยู่แล้ว")
    elif "/status" in msg:
        send_telegram("สถานะ: ทำงาน" if BOT_ACTIVE else "สถานะ: หยุดชั่วคราว")
    elif "/stop" in msg:
        BOT_ACTIVE = False
        send_telegram("หยุดบอทแล้ว")
    elif "/resume" in msg:
        BOT_ACTIVE = True
        send_telegram("เริ่มบอทอีกครั้ง")
    elif "/balance" in msg:
        send_telegram(f"ยอดเงิน: {get_balance():,.2f} USDT")
    elif "/lastprofit" in msg:
        send_telegram(f"กำไรล่าสุด: {last_profit:.2f} USDT")
    return "ok"

# --------- START -----------------------
if __name__ == "__main__":
    threading.Thread(target=monitor_trade).start()
    app.run(host="0.0.0.0", port=10000)
