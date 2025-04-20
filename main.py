import time, json, hmac, hashlib, requests, threading
from datetime import datetime
from flask import Flask, request

# === ตั้งค่าคงที่ ===
API_KEY = "e5a0da48-989e-4897-b637-d3475020fd70"
API_SECRET = "81AF116E5773A7B094DF03844731E342"
API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

SYMBOL = "BTC-USDT-SWAP"
BASE_URL = "https://www.okx.com"
LEVERAGE = 10
RISK_PER_TRADE = 0.02
PORTFOLIO_PORTION = 0.3

active_position = {
    "side": None, "entry": None, "tp": None, "sl": None, "size": None,
    "algo_id": None, "last_profit": None, "partial_done": False
}
bot_active = True
start_time = time.time()

app = Flask(__name__)

# === ฟังก์ชันช่วย ===
def get_timestamp():
    try:
        res = requests.get(BASE_URL + "/api/v5/public/time").json()
        return res["data"][0]["ts"]
    except: return str(int(time.time() * 1000))

def sign(ts, method, path, body=""):
    msg = f"{ts}{method}{path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def headers(method, path, body=""):
    ts = get_timestamp()
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sign(ts, method, path, body),
        "OK-ACCESS-TIMESTAMP": str(int(ts) / 1000),
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
            "chat_id": TELEGRAM_CHAT_ID, "text": msg
        })
    except: pass

def retry_request(method, path, body=None):
    for _ in range(3):
        try:
            h = headers(method, path, json.dumps(body) if body else "")
            url = BASE_URL + path
            r = requests.request(method, url, headers=h, json=body, timeout=5)
            return r.json()
        except Exception as e:
            telegram(f"[ERROR] Retry API: {e}")
            time.sleep(2)
    return None

# === ฟังก์ชัน API OKX ===
def get_candles(tf="1H", limit=100):
    path = f"/api/v5/market/candles?instId={SYMBOL}&bar={tf}&limit={limit}"
    r = retry_request("GET", path)
    return r["data"][::-1] if r else []

def get_price():
    candles = get_candles("1m", 1)
    return float(candles[-1][4]) if candles else 0

def get_balance():
    path = "/api/v5/account/balance?ccy=USDT"
    r = retry_request("GET", path)
    return float(r["data"][0]["details"][0]["availBal"]) if r else 0

def place_market_order(side, size):
    path = "/api/v5/trade/order"
    body = {
        "instId": SYMBOL, "tdMode": "isolated", "side": side,
        "ordType": "market", "sz": str(size), "lever": str(LEVERAGE)
    }
    r = retry_request("POST", path, body)
    telegram(f"[ORDER] {side.upper()} {SYMBOL} Size: {size}")
    return r

def place_tp_sl(entry, sl, tp, side, size):
    path = "/api/v5/trade/order-algo"
    exit_side = "sell" if side == "buy" else "buy"
    body = {
        "instId": SYMBOL, "tdMode": "isolated", "side": exit_side,
        "ordType": "oco", "slTriggerPx": f"{sl:.2f}", "slOrdPx": "-1",
        "tpTriggerPx": f"{tp:.2f}", "tpOrdPx": "-1", "sz": str(size)
    }
    r = retry_request("POST", path, body)
    if r: active_position["algo_id"] = r["data"][0]["algoId"]

def cancel_algo(algo_id):
    path = "/api/v5/trade/cancel-algos"
    body = {"instId": SYMBOL, "algoIds": [algo_id]}
    retry_request("POST", path, body)

# === Entry Strategy (ICT) ===
def detect_entry():
    m15 = get_candles("15m", 50)
    for i in range(2, len(m15)):
        high1 = float(m15[i-2][2])
        low3 = float(m15[i][3])
        if low3 > high1:
            return {"side": "buy", "entry": (low3 + high1)/2}
        low1 = float(m15[i-2][3])
        high3 = float(m15[i][2])
        if high3 < low1:
            return {"side": "sell", "entry": (high3 + low1)/2}
    return None

def swing_sl_tp(candles, side):
    if side == "buy":
        sl = min(float(c[3]) for c in candles[-5:])
        tp = max(float(c[2]) for c in candles[-5:])
    else:
        sl = max(float(c[2]) for c in candles[-5:])
        tp = min(float(c[3]) for c in candles[-5:])
    return sl, tp

# === การเทรด ===
def trade():
    if not bot_active or active_position["entry"]:
        return

    signal = detect_entry()
    if not signal: return
    side, entry = signal["side"], signal["entry"]
    h1 = get_candles("1H", 20)
    sl, tp = swing_sl_tp(h1, side)
    bal = get_balance()
    risk = bal * RISK_PER_TRADE
    size = round((risk / abs(entry - sl)), 4)

    place_market_order(side, size)
    time.sleep(1)
    place_tp_sl(entry, sl, tp, side, size)

    active_position.update({
        "side": side, "entry": entry, "tp": tp, "sl": sl,
        "size": size, "partial_done": False
    })

    telegram(f"[TRADE OPENED]\nSide: {side.upper()}\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nSize: {size}")

# === จัดการ Position: SL-BE / Partial / Trailing ===
def monitor():
    if not active_position["entry"]: return
    price = get_price()
    entry = active_position["entry"]
    tp = active_position["tp"]
    side = active_position["side"]
    sl = active_position["sl"]
    size = active_position["size"]
    algo_id = active_position["algo_id"]

    tp_half = entry + (tp - entry) * 0.5 if side == "buy" else entry - (entry - tp) * 0.5
    trailing_sl = price - (tp - entry) * 0.3 if side == "buy" else price + (entry - tp) * 0.3

    try:
        # SL to BE
        if algo_id and ((side == "buy" and price >= tp_half) or (side == "sell" and price <= tp_half)):
            cancel_algo(algo_id)
            time.sleep(1)
            place_tp_sl(entry, entry, tp, side, size)
            active_position["sl"] = entry
            active_position["algo_id"] = None
            telegram(f"[SL MOVED] SL moved to Breakeven: {entry:.2f}")

        # Partial TP
        if not active_position["partial_done"] and ((side == "buy" and price >= tp_half) or (side == "sell" and price <= tp_half)):
            place_market_order("sell" if side == "buy" else "buy", round(size/2, 4))
            active_position["partial_done"] = True
            telegram(f"[PARTIAL TP] ปิดกำไรครึ่งที่ TP1")

        # Trailing Stop
        if active_position["partial_done"]:
            cancel_algo(algo_id)
            time.sleep(1)
            place_tp_sl(entry, trailing_sl, tp, side, round(size/2, 4))
            active_position["sl"] = trailing_sl
            telegram(f"[TRAILING SL] SL ขยับตามราคา: {trailing_sl:.2f}")
    except Exception as e:
        telegram(f"[ERROR] monitor: {e}")

# === Schedule Loop ===
def loop():
    while True:
        now = datetime.utcnow()
        if now.minute % 15 == 0:
            trade()
        monitor()
        time.sleep(60)

# === Telegram Webhook ===
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    global bot_active
    msg = request.json["message"]["text"].lower()
    if "ping" in msg:
        telegram(f"ทำงานปกติ | เวลา: {datetime.utcnow()}")
    elif "uptime" in msg:
        t = round((time.time() - start_time) / 3600, 2)
        telegram(f"Uptime: {t} ชม.")
    elif "stop" in msg:
        bot_active = False
        telegram("หยุดบอทแล้ว")
    elif "resume" in msg:
        bot_active = True
        telegram("เปิดบอทต่อแล้ว")
    elif "entry" in msg:
        telegram(f"Entry: {active_position['entry']}")
    elif "tp" in msg:
        telegram(f"TP: {active_position['tp']}")
    elif "sl" in msg:
        telegram(f"SL: {active_position['sl']}")
    elif "size" in msg:
        telegram(f"Size: {active_position['size']}")
    elif "status" in msg:
        telegram(f"Side: {active_position['side']}\nEntry: {active_position['entry']}\nTP: {active_position['tp']}\nSL: {active_position['sl']}")
    elif "balance" in msg:
        telegram(f"Balance: {get_balance()} USDT")
    return "ok"

@app.route("/")
def home():
    return f"OKX ICT Bot Running {datetime.utcnow()}"

# === เริ่มระบบ ===
threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
