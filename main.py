import time
import requests
import json
import hmac
import hashlib
import base64
import threading
from flask import Flask, request
import telegram
from datetime import datetime
import schedule

# ---------------- CONFIG ----------------
API_KEY = 'e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28'
API_SECRET = '3E0BDFF2AF2EF11217C2DCC7E88400C3'
PASSPHRASE = 'Jirawat1-'
SYMBOL = 'BTC-USDT-SWAP'
LEVERAGE = 10
PORTFOLIO_PERCENTAGE = 0.3

TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
# ---------------------------------------

app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_TOKEN)
BASE_URL = "https://www.okx.com"

def get_server_timestamp():
    url = BASE_URL + "/api/v5/public/time"
    return requests.get(url).json()["data"][0]["ts"]

def sign(method, path, body=''):
    timestamp = str(int(get_server_timestamp()) / 1000)
    message = f"{timestamp}{method}{path}{body}"
    mac = hmac.new(API_SECRET.encode(), msg=message.encode(), digestmod=hashlib.sha256)
    sign = base64.b64encode(mac.digest()).decode()
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json"
    }

def get_balance():
    path = "/api/v5/account/balance"
    headers = sign("GET", path)
    res = requests.get(BASE_URL + path, headers=headers).json()
    usdt_balance = float(next(x for x in res["data"][0]["details"] if x["ccy"] == "USDT")["availBal"])
    return usdt_balance

def get_price():
    res = requests.get(BASE_URL + f"/api/v5/market/ticker?instId={SYMBOL}").json()
    return float(res["data"][0]["last"])

def place_order(side, size):
    path = "/api/v5/trade/order"
    price = get_price()
    data = {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": side,
        "ordType": "market",
        "sz": str(size),
        "lever": str(LEVERAGE)
    }
    headers = sign("POST", path, json.dumps(data))
    res = requests.post(BASE_URL + path, headers=headers, json=data).json()
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"เปิดออเดอร์ {side.upper()} ที่ราคา {price}")
    return res

def strategy():
    price = get_price()
    balance = get_balance()
    position_size = round((balance * PORTFOLIO_PERCENTAGE) * LEVERAGE / price, 3)

    # สมมุติ logic เบื้องต้น: ถ้าราคาลงต่ำกว่า 50,000 ให้ buy
    if price < 50000:
        place_order("buy", position_size)
    elif price > 60000:
        place_order("sell", position_size)

@app.route('/ping', methods=["GET"])
def ping():
    return "Bot is running"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text.lower()

    if text == "/ping":
        bot.send_message(chat_id=chat_id, text="Bot ทำงานอยู่ครับ")
    elif text == "ราคาตอนนี้":
        bot.send_message(chat_id=chat_id, text=f"ราคาปัจจุบัน: {get_price()} USDT")
    elif text == "ทุนคงเหลือ":
        bot.send_message(chat_id=chat_id, text=f"ทุน USDT: {get_balance()}")

    return "ok"

def run_bot():
    schedule.every(1).minutes.do(strategy)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)
