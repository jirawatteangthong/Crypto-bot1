# === main.py ===
import time
import requests
import hmac
import hashlib
import base64
import json
import threading
from datetime import datetime, timedelta

# === CONFIG ===
API_KEY = "0659b6f2-c86a-466a-82ec-f1a52979bc33"
API_SECRET = "CCB0A67D53315671F599050FCD712CD1"
PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 10
TRADE_PERCENTAGE = 0.3
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
CHAT_ID = "8104629569"

# === STATE ===
in_position = False
entry_price = 0.0
stop_loss_price = 0.0
take_profit_price = 0.0
breakeven_moved = False
partial_tp_done = False
order_id = None
entry_time = None

# === UTILS ===
def get_server_time():
    r = requests.get(f"{BASE_URL}/api/v5/public/time")
    return str(r.json()['data'][0]['ts'])

def sign_request(timestamp, method, request_path, body=''):
    message = f'{timestamp}{method}{request_path}{body}'
    mac = hmac.new(API_SECRET.encode(), message.encode(), digestmod=hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def okx_request(method, path, data=None, private=False):
    timestamp = get_server_time()
    headers = {}
    if private:
        body = json.dumps(data) if data else ''
        headers = {
            'OK-ACCESS-KEY': API_KEY,
            'OK-ACCESS-SIGN': sign_request(timestamp, method, path, body),
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': PASSPHRASE,
            'Content-Type': 'application/json'
        }
    url = BASE_URL + path
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers)
        res = r.json()
        if 'data' not in res:
            send_telegram(f"[DEBUG] ไม่มี 'data':\n{json.dumps(res, indent=2)}")
            return None
        return res
    except Exception as e:
        send_telegram(f"[ERROR LOOP] {str(e)}")
        return None

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except Exception as e:
        print(f"Telegram error: {e}")

def get_candles(timeframe="1m", limit=100):
    path = f"/api/v5/market/candles?instId={SYMBOL}&bar={timeframe}&limit={limit}"
    res = okx_request("GET", path)
    if not res:
        return []
    return [[float(x[1]), float(x[2]), float(x[3]), float(x[4])] for x in res['data']]

def find_swing_high_low(candles):
    high_swing = max(candles[-5:], key=lambda x: x[1])[1]
    low_swing = min(candles[-5:], key=lambda x: x[2])[2]
    return round(high_swing * 1.001, 2), round(low_swing * 0.999, 2)

def detect_fvg(candles):
    if len(candles) < 4:
        return None
    c1, c2, c3 = candles[-4], candles[-3], candles[-2]
    if c1[2] > c3[1]:
        return "bullish"
    elif c1[1] < c3[2]:
        return "bearish"
    return None

def get_balance():
    res = okx_request("GET", "/api/v5/account/balance?ccy=USDT", private=True)
    if not res: return 0
    return float(res['data'][0]['details'][0]['cashBal'])

def get_position_size(price):
    usdt = get_balance()
    qty = (usdt * TRADE_PERCENTAGE * LEVERAGE) / price
    return round(qty, 3)

def open_order(side, entry_price, sl, tp):
    global in_position, order_id, stop_loss_price, take_profit_price, entry_time
    size = get_position_size(entry_price)
    data = {
        "instId": SYMBOL,
        "tdMode": "cross",
        "side": side,
        "ordType": "market",
        "sz": str(size)
    }
    res = okx_request("POST", "/api/v5/trade/order", data, private=True)
    if res:
        in_position = True
        order_id = res['data'][0]['ordId']
        stop_loss_price = sl
        take_profit_price = tp
        entry_time = datetime.utcnow()
        send_telegram(f"[ENTRY] {side.upper()} @ {entry_price}\nSL: {sl} | TP: {tp}")

def manage_trade(current_price):
    global in_position, breakeven_moved, partial_tp_done, stop_loss_price
    if not in_position:
        return

    # Partial TP
    if not partial_tp_done and (
        (entry_price < take_profit_price and current_price >= (entry_price + (take_profit_price - entry_price) * 0.5)) or
        (entry_price > take_profit_price and current_price <= (entry_price - (entry_price - take_profit_price) * 0.5))
    ):
        partial_tp_done = True
        send_telegram("[Partial TP] 50% zone reached")

    # Break-even SL
    if not breakeven_moved and partial_tp_done:
        stop_loss_price = entry_price
        breakeven_moved = True
        send_telegram(f"[Break-even] SL moved to Entry: {entry_price}")

    # Trailing SL
    if breakeven_moved:
        trailing_sl = entry_price + (current_price - entry_price) * 0.7 if entry_price < current_price else entry_price - (entry_price - current_price) * 0.7
        if (entry_price < current_price and trailing_sl > stop_loss_price) or (entry_price > current_price and trailing_sl < stop_loss_price):
            stop_loss_price = round(trailing_sl, 2)
            send_telegram(f"[Trailing SL] SL moved to: {stop_loss_price}")

def close_position(current_price, reason):
    global in_position, order_id, breakeven_moved, partial_tp_done
    side = "sell" if entry_price < current_price else "buy"
    size = get_position_size(entry_price)
    data = {
        "instId": SYMBOL,
        "tdMode": "cross",
        "side": side,
        "ordType": "market",
        "sz": str(size)
    }
    okx_request("POST", "/api/v5/trade/order", data, private=True)
    send_telegram(f"[EXIT] @ {current_price}\n{reason}")
    in_position = False
    breakeven_moved = False
    partial_tp_done = False

def main_loop():
    send_telegram("[BOT STARTED] เทรดตาม H4 > M15 > M1")

    while True:
        try:
            candles_h4 = get_candles("4H")
            candles_m15 = get_candles("15m")
            candles_m1 = get_candles("1m")

            signal = detect_fvg(candles_m15)
            current_price = candles_m1[-1][3]
            high, low = find_swing_high_low(candles_m15)

            if not in_position:
                if signal == "bullish":
                    open_order("buy", current_price, low, current_price + (high - low) * 1.5)
                elif signal == "bearish":
                    open_order("sell", current_price, high, current_price - (high - low) * 1.5)
            else:
                manage_trade(current_price)
                if (entry_price < current_price and current_price <= stop_loss_price) or \
                   (entry_price > current_price and current_price >= stop_loss_price):
                    close_position(current_price, "[SL HIT]")
                elif (entry_price < current_price and current_price >= take_profit_price) or \
                     (entry_price > current_price and current_price <= take_profit_price):
                    close_position(current_price, "[TP HIT]")

            time.sleep(20)

        except Exception as e:
            send_telegram(f"[ERROR LOOP] {e}")
            time.sleep(30)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        send_telegram("[BOT STOPPED]")
