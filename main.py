import time, requests, hmac, hashlib, json
from datetime import datetime
from threading import Thread
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler

# ---------------- CONFIG ----------------
API_KEY = "e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28"
API_SECRET = "3E0BDFF2AF2EF11217C2DCC7E88400C3"
PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 10
TRADE_PERCENTAGE = 0.3

TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
CHAT_ID = "8104629569"
bot = Bot(token=TELEGRAM_TOKEN)

# ---------------- STATE ----------------
in_position = False
entry_price = 0.0
stop_loss_price = 0.0
take_profit_price = 0.0

# ----------------- UTILITIES ----------------
def sign_request(ts, method, path, body):
    msg = f"{ts}{method}{path}{body}"
    return base64.b64encode(hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).digest()).decode()

def get_server_time():
    try:
        res = requests.get(f"{BASE_URL}/api/v5/public/time")
        return res.json()["data"][0]["ts"]
    except:
        return str(int(time.time() * 1000))

def okx_request(method, path, data=None, private=False):
    ts = get_server_time()
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sign_request(ts, method, path, json.dumps(data) if data else ''),
        'OK-ACCESS-TIMESTAMP': ts,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    } if private else {}

    try:
        if method == "GET":
            r = requests.get(BASE_URL + path, headers=headers)
        elif method == "POST":
            r = requests.post(BASE_URL + path, headers=headers, json=data)
        elif method == "DELETE":
            r = requests.delete(BASE_URL + path, headers=headers)
        res = r.json()
        if 'data' not in res:
            send_telegram(f"[DEBUG] ไม่มี 'data':\n{json.dumps(res, indent=2)}")
            return None
        return res
    except Exception as e:
        send_telegram(f"[ERROR] {e}")
        return None

def get_balance():
    res = okx_request("GET", "/api/v5/account/balance", private=True)
    try:
        for d in res['data'][0]['details']:
            if d['ccy'] == 'USDT':
                return float(d['availEq'])
    except: return 0.0

def get_price():
    res = okx_request("GET", f"/api/v5/market/ticker?instId={SYMBOL}")
    try:
        return float(res["data"][0]["last"])
    except: return 0.0

def send_telegram(msg):
    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
    except: pass

# ----------------- TRADE CORE ----------------
def open_order():
    global in_position, entry_price, stop_loss_price, take_profit_price
    price = get_price()
    balance = get_balance()
    qty = round((balance * TRADE_PERCENTAGE * LEVERAGE) / price, 3)
    entry_price = price
    stop_loss_price = round(price * 0.985, 2)  # SL ใต้ swing
    take_profit_price = round(price * 1.03, 2)

    okx_request("POST", "/api/v5/account/set-leverage", {
        "instId": SYMBOL, "lever": str(LEVERAGE), "mgnMode": "isolated"
    }, private=True)

    okx_request("POST", "/api/v5/trade/order", {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": "buy",
        "ordType": "market",
        "sz": str(qty)
    }, private=True)

    in_position = True
    send_telegram(f"[ENTRY]\nเข้าออเดอร์ที่ {price}\nSL: {stop_loss_price}\nTP: {take_profit_price}")

def close_order():
    global in_position
    okx_request("POST", "/api/v5/trade/close-position", {
        "instId": SYMBOL, "mgnMode": "isolated", "posSide": "long"
    }, private=True)
    in_position = False
    send_telegram(f"[EXIT]\nปิดออเดอร์ที่ราคา {get_price()}")

# ---------------- SIGNAL ----------------
def get_entry_signal():
    now = datetime.utcnow()
    if now.hour in [1, 2, 3]:  # เวลา ICT/London
        price = get_price()
        if price < 70000:  # ตัวอย่าง logic จำลอง
            send_telegram(f"[SWING] ราคาต่ำกว่า Swing High: {price}")
            return True
    return False

# ---------------- MONITOR ----------------
def monitor_loop():
    global in_position
    send_telegram("เริ่มทำงานบอทแล้ว")
    while True:
        try:
            price = get_price()
            if in_position:
                if price >= take_profit_price or price <= stop_loss_price:
                    close_order()
            else:
                if get_entry_signal():
                    open_order()
            time.sleep(15)
        except Exception as e:
            send_telegram(f"[ERROR LOOP] {e}")
            time.sleep(30)

# ---------------- TELEGRAM COMMAND ----------------
def start(update: Update, context): update.message.reply_text("บอททำงานอยู่")
def status(update: Update, context): update.message.reply_text(f"สถานะ: {'เข้าออเดอร์' if in_position else 'รอจังหวะ'}\nราคาปัจจุบัน: {get_price()}")
def price(update: Update, context): update.message.reply_text(f"ราคาล่าสุด: {get_price()}")

def telegram_bot():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("price", price))
    updater.start_polling()
    updater.idle()

# ---------------- MAIN ----------------
if __name__ == "__main__":
    Thread(target=telegram_bot).start()
    Thread(target=monitor_loop).start()
