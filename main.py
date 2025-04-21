import time, hmac, hashlib, base64, json, requests
from datetime import datetime, timedelta

# ------------------- OKX CONFIG -------------------
API_KEY = "e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28"
API_SECRET = "3E0BDFF2AF2EF11217C2DCC7E88400C3"
PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 10
TRADE_PERCENTAGE = 0.3

# ---------------- TELEGRAM CONFIG ----------------
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
CHAT_ID = "8104629569"

# ---------------- SYSTEM STATE ----------------
in_position = False
entry_price = 0.0
qty = 0.0
sl_price = 0.0
tp1_price = 0.0
tp2_price = 0.0
tp1_hit = False

# ---------------- UTILS -------------------
def get_server_time():
    r = requests.get(f"{BASE_URL}/api/v5/public/time")
    return r.json()['data'][0]['ts']

def sign_request(timestamp, method, path, body=""):
    message = f"{timestamp}{method}{path}{body}"
    mac = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def okx_request(method, path, data=None, private=False):
    timestamp = get_server_time()
    headers = {
        "Content-Type": "application/json"
    }
    if private:
        body = json.dumps(data) if data else ""
        headers.update({
            "OK-ACCESS-KEY": API_KEY,
            "OK-ACCESS-SIGN": sign_request(timestamp, method, path, body),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        })

    url = BASE_URL + path
    r = requests.request(method, url, headers=headers, json=data)
    res = r.json()
    if "data" not in res:
        send_telegram(f"[ERROR] ไม่มี 'data': {json.dumps(res)}")
        return None
    return res

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def get_price():
    res = okx_request("GET", f"/api/v5/market/ticker?instId={SYMBOL}")
    if res: return float(res["data"][0]["last"])
    return 0.0

def get_balance():
    res = okx_request("GET", "/api/v5/account/balance", private=True)
    if res:
        for d in res["data"][0]["details"]:
            if d["ccy"] == "USDT":
                return float(d["availEq"])
    return 0.0

def get_swing_price(buffer=50):
    candles = okx_request("GET", f"/api/v5/market/candles?instId={SYMBOL}&bar=1m&limit={buffer}")
    if candles:
        prices = [float(c[2]) for c in candles["data"]]  # high
        highs = max(prices)
        lows = min([float(c[3]) for c in candles["data"]])  # low
        return highs, lows
    return 0.0, 0.0

def set_leverage():
    okx_request("POST", "/api/v5/account/set-leverage", {
        "instId": SYMBOL,
        "lever": str(LEVERAGE),
        "mgnMode": "isolated"
    }, private=True)

def open_order():
    global in_position, entry_price, qty, sl_price, tp1_price, tp2_price, tp1_hit
    if in_position:
        return

    price = get_price()
    balance = get_balance()
    qty = round((balance * TRADE_PERCENTAGE * LEVERAGE) / price, 3)
    highs, lows = get_swing_price()

    sl_price = round(lows * 0.998, 2)
    tp1_price = round(price * 1.015, 2)
    tp2_price = round(price * 1.03, 2)
    entry_price = price
    tp1_hit = False

    set_leverage()

    okx_request("POST", "/api/v5/trade/order", {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": "buy",
        "ordType": "market",
        "sz": str(qty)
    }, private=True)

    in_position = True
    send_telegram(f"เข้าออเดอร์ BUY {qty} ที่ราคา {price}\nSL: {sl_price}\nTP1: {tp1_price}, TP2: {tp2_price}")

def close_position(reason=""):
    global in_position, qty
    if not in_position:
        return
    okx_request("POST", "/api/v5/trade/order", {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": "sell",
        "ordType": "market",
        "sz": str(qty)
    }, private=True)

    price = get_price()
    pnl = (price - entry_price) * qty
    send_telegram(f"ปิดออเดอร์ที่ {price} | PnL: {round(pnl, 2)}\n{reason}")
    in_position = False

def monitor():
    global in_position, tp1_hit, sl_price
    while True:
        if in_position:
            price = get_price()
            if not tp1_hit and price >= tp1_price:
                tp1_hit = True
                sl_price = round(entry_price * 1.001, 2)
                send_telegram(f"ถึง TP1 แล้ว ขยับ SL มา BE+: {sl_price}")
            elif price >= tp2_price:
                close_position("ถึง TP2")
            elif price <= sl_price:
                close_position("โดน SL")
        else:
            if check_entry_signal():
                open_order()
        time.sleep(15)

def check_entry_signal():
    now = datetime.utcnow()
    if now.hour in [1, 2, 3]:  # ช่วง London session
        price = get_price()
        if price < 70000:  # ตัวอย่าง logic ICT (ควรแทนด้วย 1D > H1 > M15 จริง)
            return True
    return False

# ---------------- START BOT -------------------
if __name__ == "__main__":
    try:
        send_telegram("บอทเริ่มทำงานแล้ว")
        monitor()
    except Exception as e:
        send_telegram(f"บอทหยุดทำงาน: {str(e)}")
