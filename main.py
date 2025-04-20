import time
import json
import hmac
import hashlib
import requests
import threading
import schedule
from datetime import datetime
from flask import Flask, request

# === ตั้งค่าหลัก ===
API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

SYMBOL = "BTC-USDT-SWAP"
BASE_URL = "https://www.okx.com"
LEVERAGE = 10
USE_PORTFOLIO_PERCENT = 0.30
RISK_PER_TRADE = 0.02

# ตัวแปรสถานะ
active_position = {
    "side": None,
    "entry": None,
    "tp": None,
    "sl": None,
    "size": None,
    "algo_id": None,
    "last_profit": None,
    "partial_taken": False
}
bot_active = True
start_time = time.time()

# === ระบบ Sign สำหรับ OKX ===
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
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print("ส่ง Telegram ไม่สำเร็จ:", e)
        # === ดึงราคาและข้อมูลแท่งเทียน ===
def get_price():
    candles = get_candles("1m", 1)
    return float(candles[-1][4])

def get_candles(tf="1H", limit=100, retries=3):
    path = f"/api/v5/market/candles?instId={SYMBOL}&bar={tf}&limit={limit}"
    for _ in range(retries):
        try:
            res = requests.get(BASE_URL + path, headers=get_headers("GET", path)).json()
            return res["data"][::-1]
        except:
            time.sleep(1)
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

def get_open_orders():
    path = f"/api/v5/trade/orders-pending?instId={SYMBOL}"
    try:
        res = requests.get(BASE_URL + path, headers=get_headers("GET", path)).json()
        return res["data"]
    except:
        return []

# === ฟังก์ชันสั่งออเดอร์และ TP/SL ===
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
        send_telegram(f"[ORDER] {side.upper()} {SYMBOL} | Size: {size}")
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

# === วิเคราะห์ Entry ตาม ICT 1D > H1 > M15 ===
def detect_entry_signal():
    m15 = get_candles("15m", 50)
    if not m15:
        return None
    for i in range(2, len(m15)):
        high1 = float(m15[i - 2][2])
        low3 = float(m15[i][3])
        if low3 > high1:
            return {"side": "buy", "entry": (low3 + high1) / 2}
        low1 = float(m15[i - 2][3])
        high3 = float(m15[i][2])
        if high3 < low1:
            return {"side": "sell", "entry": (high3 + low1) / 2}
    return None

def find_swing_levels(candles, side):
    if not candles:
        return (0, 0)
    if side == "buy":
        sl = min(float(c[3]) for c in candles[-5:])
        tp = max(float(c[2]) for c in candles[-5:])
    else:
        sl = max(float(c[2]) for c in candles[-5:])
        tp = min(float(c[3]) for c in candles[-5:])
    return sl, tp
    # === ตัวแปรสำหรับติดตามสถานะ ===
active_position = {
    "side": None,
    "entry": 0,
    "sl": 0,
    "tp": 0,
    "size": 0,
    "algo_id": None,
    "half_closed": False
}

def monitor_position():
    if not active_position["side"]:
        return

    price = get_price()
    entry = active_position["entry"]
    tp = active_position["tp"]
    sl = active_position["sl"]
    side = active_position["side"]
    size = float(active_position["size"])

    # === Partial TP ===
    tp_half = entry + (tp - entry) * 0.5 if side == "buy" else entry - (entry - tp) * 0.5
    if not active_position["half_closed"]:
        if (side == "buy" and price >= tp_half) or (side == "sell" and price <= tp_half):
            close_half_position()
            active_position["half_closed"] = True
            send_telegram("[TP] Partial TP สำเร็จ ปิดกำไรครึ่งหนึ่ง")

    # === Trailing Stop ===
    trail_gap = abs(tp - entry) * 0.3  # 30% trailing
    new_sl = price - trail_gap if side == "buy" else price + trail_gap
    if (side == "buy" and new_sl > sl) or (side == "sell" and new_sl < sl):
        cancel_algo_order(active_position["algo_id"])
        place_tp_sl(entry, new_sl, tp, side, size / 2 if active_position["half_closed"] else size)
        active_position["sl"] = new_sl
        send_telegram(f"[TRAILING] SL ขยับใหม่เป็น {new_sl:.2f}")

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

def trading_bot():
    while True:
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

        time.sleep(10)
        # === Kill Switch ตัวแปร ===
bot_active = True
start_time = time.time()

# === Webhook สำหรับรับข้อความจาก Telegram ===
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    global bot_active
    update = request.get_json()
    message = update.get('message', {}).get('text', '')
    chat_id = update.get('message', {}).get('chat', {}).get('id', '')

    if not message:
        return "ok", 200

    if message == '/ping':
        return send_telegram("pong", chat_id), 200
    elif message == '/uptime':
        uptime = time.time() - start_time
        return send_telegram(f"Bot ทำงานมาแล้ว {int(uptime)} วินาที", chat_id), 200
    elif message.lower() == 'stop bot':
        bot_active = False
        return send_telegram("บอทถูกหยุดชั่วคราวแล้ว", chat_id), 200
    elif message.lower() == 'resume bot':
        bot_active = True
        return send_telegram("บอทกลับมาทำงานแล้ว", chat_id), 200
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
        return send_telegram(msg.strip(), chat_id), 200

    return "ok", 200

# === Thread สำหรับรันบอทเทรดใน background ===
def run_trading_bot():
    while True:
        try:
            if bot_active:
                trading_bot()
        except Exception as e:
            send_telegram(f"[CRASH] ระบบหยุดทำงาน: {str(e)}")
        time.sleep(10)

# === main ===
if __name__ == '__main__':
    Thread(target=run_trading_bot).start()
    app.run(host='0.0.0.0', port=5000)
