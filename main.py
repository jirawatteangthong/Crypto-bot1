import time
import requests
import hmac
import hashlib
import base64
import json
import threading
from datetime import datetime

# =============== OKX CONFIG ==================
API_KEY = "0659b6f2-c86a-466a-82ec-f1a52979bc33"
API_SECRET = "CCB0A67D53315671F599050FCD712CD1"
PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 10
TRADE_PERCENTAGE = 0.3

# =============== TELEGRAM ====================
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
CHAT_ID = "8104629569"

# =============== STATE =======================
in_position = False
entry_price = 0.0
order_id = None
stop_loss_price = 0.0
take_profit_price = 0.0
breakeven_moved = False
partial_tp_hit = False
running = True

# =============== UTILS =======================
def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_server_time():
    r = requests.get(f"{BASE_URL}/api/v5/public/time")
    return r.json()['data'][0]['ts']

def sign_request(timestamp, method, request_path, body=''):
    prehash = f"{timestamp}{method}{request_path}{body}"
    return base64.b64encode(
        hmac.new(
            API_SECRET.encode('utf-8'),
            prehash.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode()

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
        r = requests.request(method, url, headers=headers, json=data)
        res_json = r.json()
        if 'data' not in res_json:
            send_telegram(f"[DEBUG] ไม่มี 'data':\n{json.dumps(res_json, indent=2)}")
            return None
        return res_json
    except Exception as e:
        send_telegram(f"[ERROR LOOP] {e}")
        return None

# =============== PRICE + BALANCE ================
def get_price():
    res = okx_request("GET", f"/api/v5/market/ticker?instId={SYMBOL}")
    return float(res["data"][0]["last"]) if res else 0

def get_balance():
    res = okx_request("GET", "/api/v5/account/balance", private=True)
    if res:
        for d in res["data"][0]["details"]:
            if d["ccy"] == "USDT":
                return float(d["availEq"])
    return 0

# =============== STRATEGY =======================
def get_swing_levels():
    # จำลอง Swing H/L — ใช้ M15/M1 จริงในเวอร์ชันต่อยอด
    price = get_price()
    return round(price * 0.985, 2), round(price * 1.015, 2)  # SL low / high

def get_entry_signal():
    now = datetime.utcnow()
    if now.minute % 15 == 0:
        price = get_price()
        if price < 70000:  # ตัวอย่าง logic
            return True
    return False

# =============== ORDER MANAGEMENT ===============
def open_order():
    global in_position, entry_price, stop_loss_price, take_profit_price
    price = get_price()
    balance = get_balance()
    qty = round((balance * TRADE_PERCENTAGE * LEVERAGE) / price, 3)
    sl, tp = get_swing_levels()
    entry_price = price
    stop_loss_price = sl
    take_profit_price = tp

    okx_request("POST", "/api/v5/account/set-leverage", {
        "instId": SYMBOL,
        "lever": str(LEVERAGE),
        "mgnMode": "isolated"
    }, private=True)

    res = okx_request("POST", "/api/v5/trade/order", {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": "buy",
        "ordType": "market",
        "sz": str(qty)
    }, private=True)

    if res:
        send_telegram(f"เข้าออเดอร์ที่ {price}\nSL: {sl}, TP: {tp}")
        in_position = True

def close_position(reason):
    global in_position, breakeven_moved, partial_tp_hit
    okx_request("POST", "/api/v5/trade/close-position", {
        "instId": SYMBOL,
        "mgnMode": "isolated",
        "posSide": "long"
    }, private=True)
    send_telegram(f"ปิดออเดอร์ ({reason}) ที่ราคา {get_price()}")
    in_position = False
    breakeven_moved = False
    partial_tp_hit = False

# =============== MONITORING ======================
def monitor_trade():
    global in_position, breakeven_moved, partial_tp_hit
    send_telegram("บอทเริ่มทำงานแล้ว")
    while running:
        try:
            if in_position:
                price = get_price()
                profit_range = take_profit_price - entry_price

                # Partial TP
                if not partial_tp_hit and price >= entry_price + profit_range * 0.5:
                    partial_tp_hit = True
                    send_telegram(f"[PARTIAL TP] ราคาถึง 50% TP: {price}")

                # Break-even
                if not breakeven_moved and price >= entry_price + profit_range * 0.5:
                    stop_loss_price = entry_price
                    breakeven_moved = True
                    send_telegram("[BREAK-EVEN] ขยับ SL ไปที่จุดเข้า")

                # TP/SL
                if price >= take_profit_price:
                    close_position("TP")
                elif price <= stop_loss_price:
                    close_position("SL")

            else:
                if get_entry_signal():
                    open_order()

            time.sleep(10)
        except Exception as e:
            send_telegram(f"[ERROR LOOP] {e}")
            time.sleep(15)

# =============== ENTRY ===========================
if __name__ == "__main__":
    try:
        t = threading.Thread(target=monitor_trade)
        t.start()
    except Exception as e:
        send_telegram(f"[ERROR START] {e}")
