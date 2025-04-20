import time
import json
import hmac
import hashlib
import requests
import threading
import schedule
import os
from datetime import datetime
from flask import Flask, request

# === Flask App ===
app = Flask(__name__)

# === ตั้งค่าหลัก ===
API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

SYMBOL = "BTC-USDT-SWAP"
BASE_URL = "https://www.okx.com"
LEVERAGE = 10

active_position = {
    "side": None,
    "entry": 0,
    "sl": 0,
    "tp": 0,
    "size": 0,
    "algo_id": None,
    "half_closed": False
}
bot_active = True
start_time = time.time()

# === ระบบ Sign OKX ===
def sign(timestamp, method, request_path, body=""):
    msg = f"{timestamp}{method}{request_path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def get_headers(method, path, body=""):
    timestamp = str(time.time())
    signature = sign(timestamp, method, path, body)
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

# === Telegram แจ้งเตือน ===
def send_telegram(msg, chat_id=TELEGRAM_CHAT_ID):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg})
    except Exception as e:
        print("ส่ง Telegram ไม่สำเร็จ:", e)

# === ดึงราคา / ข้อมูล ===
def get_price():
    candles = get_candles("1m", 1)
    return float(candles[-1][4]) if candles else 0

def get_candles(tf="15m", limit=50):
    path = f"/api/v5/market/candles?instId={SYMBOL}&bar={tf}&limit={limit}"
    try:
        res = requests.get(BASE_URL + path, headers=get_headers("GET", path)).json()
        return res["data"][::-1]
    except:
        send_telegram("[ERROR] ดึงข้อมูลแท่งเทียนล้มเหลว")
        return []

def get_balance():
    path = "/api/v5/account/balance?ccy=USDT"
    try:
        res = requests.get(BASE_URL + path, headers=get_headers("GET", path)).json()
        return float(res['data'][0]['details'][0]['availBal'])
    except:
        send_telegram("[ERROR] ดึง Balance ไม่ได้")
        return 0

# === ออเดอร์ ===
def place_order(side, size):
    path = "/api/v5/trade/order"
    data = {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": side,
        "ordType": "market",
        "sz": str(size),
        "lever": str(LEVERAGE)
    }
    body = json.dumps(data)
    try:
        res = requests.post(BASE_URL + path, headers=get_headers("POST", path, body), data=body).json()
        send_telegram(f"[ORDER] {side.upper()} | Size: {size}")
        return res
    except:
        send_telegram("[ERROR] วางคำสั่ง Order ไม่สำเร็จ")
        return {}

def place_tp_sl(entry, sl, tp, side, size):
    path = "/api/v5/trade/order-algo"
    exit_side = "sell" if side == "buy" else "buy"
    data = {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": exit_side,
        "ordType": "oco",
        "slTriggerPx": f"{sl:.2f}",
        "slOrdPx": "-1",
        "tpTriggerPx": f"{tp:.2f}",
        "tpOrdPx": "-1",
        "sz": str(size)
    }
    body = json.dumps(data)
    try:
        res = requests.post(BASE_URL + path, headers=get_headers("POST", path, body), data=body).json()
        active_position["algo_id"] = res["data"][0]["algoId"]
        return res
    except:
        send_telegram("[ERROR] วาง TP/SL ไม่สำเร็จ")
        return {}

def cancel_algo_order(algo_id):
    path = "/api/v5/trade/cancel-algos"
    data = {"instId": SYMBOL, "algoIds": [algo_id]}
    body = json.dumps(data)
    try:
        return requests.post(BASE_URL + path, headers=get_headers("POST", path, body), data=body).json()
    except:
        send_telegram("[ERROR] ยกเลิก Algo Order ไม่สำเร็จ")
        return {}

# === ระบบวิเคราะห์ ICT ===
def detect_entry_signal():
    m15 = get_candles("15m", 50)
    if not m15:
        return None
    for i in range(2, len(m15)):
        high1 = float(m15[i - 2][2])
        low3 = float(m15[i][3])
        if low3 > high1:
            return {"side": "buy"}
        low1 = float(m15[i - 2][3])
        high3 = float(m15[i][2])
        if high3 < low1:
            return {"side": "sell"}
    return None

def find_swing_levels(candles, side):
    if side == "buy":
        sl = min(float(c[3]) for c in candles[-5:])
        tp = max(float(c[2]) for c in candles[-5:])
    else:
        sl = max(float(c[2]) for c in candles[-5:])
        tp = min(float(c[3]) for c in candles[-5:])
    return sl, tp

# === จัดการ Position ===
def monitor_position():
    if not active_position["side"]:
        return
    price = get_price()
    entry = active_position["entry"]
    tp = active_position["tp"]
    sl = active_position["sl"]
    side = active_position["side"]
    size = float(active_position["size"])

    tp_half = entry + (tp - entry) * 0.5 if side == "buy" else entry - (entry - tp) * 0.5
    if not active_position["half_closed"]:
        if (side == "buy" and price >= tp_half) or (side == "sell" and price <= tp_half):
            close_half_position()
            active_position["half_closed"] = True
            send_telegram("[TP] Partial TP สำเร็จ")

    trail_gap = abs(tp - entry) * 0.3
    new_sl = price - trail_gap if side == "buy" else price + trail_gap
    if (side == "buy" and new_sl > sl) or (side == "sell" and new_sl < sl):
        cancel_algo_order(active_position["algo_id"])
        place_tp_sl(entry, new_sl, tp, side, size / 2 if active_position["half_closed"] else size)
        active_position["sl"] = new_sl
        send_telegram(f"[TRAILING SL] ขยับ SL ใหม่: {new_sl:.2f}")

def close_half_position():
    path = "/api/v5/trade/order"
    size = float(active_position["size"]) / 2
    side = "sell" if active_position["side"] == "buy" else "buy"
    data = {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": side,
        "ordType": "market",
        "sz": str(size)
    }
    body = json.dumps(data)
    try:
        requests.post(BASE_URL + path, headers=get_headers("POST", path, body), data=body)
    except:
        send_telegram("[ERROR] ปิด Partial TP ไม่สำเร็จ")

# === ระบบหลัก ===
def trading_bot():
    try:
        if not active_position["side"]:
            signal = detect_entry_signal()
            if signal:
                entry_price = get_price()
                candles = get_candles("15m", 10)
                sl, tp = find_swing_levels(candles, signal["side"])
                balance = get_balance()
                size = round((balance * 0.3 * LEVERAGE) / entry_price, 3)

                res = place_order(signal["side"], size)
                if res.get("data"):
                    active_position.update({
                        "side": signal["side"],
                        "entry": entry_price,
                        "sl": sl,
                        "tp": tp,
                        "size": size,
                        "half_closed": False
                    })
                    place_tp_sl(entry_price, sl, tp, signal["side"], size)
        else:
            monitor_position()
    except Exception as e:
        send_telegram(f"[BOT ERROR] {str(e)}")

# === Webhook Telegram ===
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    global bot_active
    update = request.get_json()
    message = update.get('message', {}).get('text', '')
    chat_id = update.get('message', {}).get('chat', {}).get('id', TELEGRAM_CHAT_ID)

    if message == '/ping':
        send_telegram("pong", chat_id)
    elif message == '/uptime':
        uptime = time.time() - start_time
        send_telegram(f"บอททำงานมาแล้ว {int(uptime)} วินาที", chat_id)
    elif message.lower() == 'stop bot':
        bot_active = False
        send_telegram("บอทถูกหยุดชั่วคราวแล้ว", chat_id)
    elif message.lower() == 'resume bot':
        bot_active = True
        send_telegram("บอทกลับมาทำงานแล้ว", chat_id)
    elif message.lower() == 'status':
        if active_position["side"]:
            msg = f"""
[STATUS]
Side: {active_position["side"]}
Entry: {active_position["entry"]}
TP: {active_position["tp"]}
SL: {active_position["sl"]}
Size: {active_position["size"]}
Half Closed: {active_position["half_closed"]}
"""
        else:
            msg = "ยังไม่มี Position ที่เปิดอยู่ตอนนี้"
        send_telegram(msg.strip(), chat_id)
    return "ok", 200

# === รันบอทแบบ Background Thread ===
def run_bot():
    while True:
        if bot_active:
            trading_bot()
        time.sleep(10)

# === Main ===
if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
