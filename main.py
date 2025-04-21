import time
import requests
import hmac
import hashlib
import base64
import json
import threading
from datetime import datetime

# ------------------- OKX CONFIG -------------------
API_KEY = "e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28"
API_SECRET = "3E0BDFF2AF2EF11217C2DCC7E88400C3"
PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 10
TRADE_PERCENTAGE = 0.3  # 30% ของพอร์ต

# ---------------- TELEGRAM CONFIG ----------------
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
CHAT_ID = "8104629569"

# ---------------- SYSTEM STATE ----------------
in_position = False
entry_price = 0.0
order_id = None
stop_loss_price = 0.0
take_profit_price = 0.0

# ----------------- UTILS -------------------
def get_server_time():
    response = requests.get(f"{BASE_URL}/api/v5/public/time")
    return str(response.json()['data'][0]['ts'])

def sign_request(timestamp, method, request_path, body=''):
    message = f'{timestamp}{method}{request_path}{body}'
    mac = hmac.new(API_SECRET.encode(), message.encode(), digestmod=hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, json=payload)

def okx_request(method, path, data=None, private=False):
    timestamp = get_server_time()
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sign_request(timestamp, method, path, json.dumps(data) if data else ''),
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    } if private else {}

    url = BASE_URL + path
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers)

        res_json = r.json()

        # Debug: ดู response จริงๆ ถ้าไม่มี 'data'
        if 'data' not in res_json:
            send_telegram(f"[ERROR] ไม่พบ 'data':\n{res_json}")
            return None

        return res_json
    except Exception as e:
        send_telegram(f"[ERROR] Exception: {e}")
        return None

# ----------------- TRADING LOGIC -------------------
def get_balance():
    res = okx_request("GET", "/api/v5/account/balance", private=True)
    if res and "data" in res:
        for d in res["data"][0]["details"]:
            if d["ccy"] == "USDT":
                return float(d["availEq"])
    return 0.0

def get_price():
    res = okx_request("GET", f"/api/v5/market/ticker?instId={SYMBOL}")
    if res and "data" in res:
        return float(res["data"][0]["last"])
    return 0.0

def close_position():
    global in_position
    res = okx_request("POST", "/api/v5/trade/close-position", {
        "instId": SYMBOL,
        "mgnMode": "isolated",
        "posSide": "long"
    }, private=True)
    in_position = False
    send_telegram(f"ปิดออเดอร์ที่ราคา {get_price()}")

def open_order():
    global in_position, entry_price, stop_loss_price, take_profit_price

    price = get_price()
    balance = get_balance()
    qty = round((balance * TRADE_PERCENTAGE * LEVERAGE) / price, 3)
    entry_price = price
    sl = round(price * 0.985, 2)
    tp = round(price * 1.03, 2)
    stop_loss_price = sl
    take_profit_price = tp

    # Set leverage
    okx_request("POST", "/api/v5/account/set-leverage", {
        "instId": SYMBOL,
        "lever": str(LEVERAGE),
        "mgnMode": "isolated"
    }, private=True)

    # Place market order
    order = okx_request("POST", "/api/v5/trade/order", {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": "buy",
        "ordType": "market",
        "sz": str(qty)
    }, private=True)

    in_position = True
    send_telegram(f"เปิดออเดอร์ที่ราคา {price}\nSL: {sl}\nTP: {tp}")

def monitor_trade():
    global in_position, stop_loss_price, take_profit_price

    while True:
        if in_position:
            price = get_price()

            # Take Profit
            if price >= take_profit_price:
                close_position()
                time.sleep(3)
                continue

            # Stop Loss
            if price <= stop_loss_price:
                close_position()
                time.sleep(3)
                continue

        else:
            signal = get_entry_signal()
            if signal:
                open_order()

        time.sleep(15)

# ----------------- SIGNAL STRATEGY (ICT แนวทางง่าย) -------------------
def get_entry_signal():
    now = datetime.utcnow()
    if now.hour in [1, 2, 3]:  # เงื่อนไขเวลาซื้อขาย เช่น เปิดออเดอร์ช่วง London
        # ตัวอย่างกลยุทธ์จำลอง: ถ้าราคาต่ำกว่า EMA (จำลอง)
        price = get_price()
        if price < 70000:  # เงื่อนไขจำลอง ควรแทนที่ด้วย logic 1D > H1 > M15
            return True
    return False

# ----------------- START BOT -------------------
def run_bot():
    send_telegram("บอทเริ่มทำงานแล้ว")
    monitor_trade()

if __name__ == "__main__":
    try:
        run_bot()
    except Exception as e:
        send_telegram(f"บอทหยุดทำงาน: {str(e)}")
