import ccxt
import requests
import time
import datetime
from config import *
from telegram import Bot

# ตัวแปรทุน
capital = START_CAPITAL
position_open = False

# ตัวแปรจำกัดจำนวนไม้ต่อวัน
trade_count = 0
last_trade_date = None

# Connect to OKX
exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Telegram Bot
bot = Bot(token=TELEGRAM_TOKEN)

# === STRATEGY CONFIG ===
EMA_TF = '1h'       # ดูเทรนด์จาก H1
EMA_PERIOD = 50     # EMA50
ENTRY_TF = '15m'    # หาจุดเข้า M15
MICRO_TF = '1m'     # Confirm จุดเข้า M1

LEVERAGE = 15
START_CAPITAL = 20
DAILY_MAX_TRADES = 1
CHECK_INTERVAL = 30  # วินาที

# === Functions ===

def fetch_ema():
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=EMA_TF, limit=EMA_PERIOD+1)
    closes = [bar[4] for bar in bars]
    ema = sum(closes[-EMA_PERIOD:]) / EMA_PERIOD
    return ema

def fetch_price():
    ticker = exchange.fetch_ticker(SYMBOL)
    return ticker['last']

def send_telegram(message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def calculate_macd(data, fast=12, slow=26, signal=9):
    def ema(values, period):
        k = 2 / (period + 1)
        ema_val = values[0]
        result = []
        for price in values:
            ema_val = price * k + ema_val * (1 - k)
            result.append(ema_val)
        return result
    macd_line = [f - s for f, s in zip(ema(data, fast), ema(data, slow))]
    signal_line = ema(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, hist

def check_entry():
    ema_now = fetch_ema()
    bars_entry = exchange.fetch_ohlcv(SYMBOL, timeframe=ENTRY_TF, limit=50)
    closes_entry = [bar[4] for bar in bars_entry]

    bars_micro = exchange.fetch_ohlcv(SYMBOL, timeframe=MICRO_TF, limit=50)
    closes_micro = [bar[4] for bar in bars_micro]

    current_price = fetch_price()

    trend_up = current_price > ema_now

    macd, signal, hist = calculate_macd(closes_micro)

    cross_up = macd[-2] < signal[-2] and macd[-1] > signal[-1]
    cross_down = macd[-2] > signal[-2] and macd[-1] < signal[-1]

    if trend_up and cross_up:
        return "long", current_price
    elif not trend_up and cross_down:
        return "short", current_price
    else:
        return None, None

def place_order(direction, price):
    global capital, position_open

    size = round((capital * LEVERAGE) / price, 3)
    side = 'buy' if direction == "long" else 'sell'
    sl_side = 'sell' if side == 'buy' else 'buy'

    sl_price = round(price * (0.995 if direction == "long" else 1.005), 2)
    tp_price = round(price * (1.01 if direction == "long" else 0.99), 2)

    # Place Market Order
    exchange.create_market_order(SYMBOL, side, size)
    
    # Place OCO (Take Profit + Stop Loss)
    exchange.private_post_trade_order_algo({
        'instId': SYMBOL,
        'tdMode': 'cross',
        'side': sl_side,
        'ordType': 'oco',
        'sz': size,
        'tpTriggerPx': tp_price,
        'tpOrdPx': '-1',
        'slTriggerPx': sl_price,
        'slOrdPx': '-1'
    })

    position_open = True
    send_telegram(f"[ENTRY] {direction.upper()} @ {price}\nSize: {size}\nTP: {tp_price}\nSL: {sl_price}")

def monitor_position():
    global capital, position_open

    orders = exchange.fetch_closed_orders(SYMBOL, limit=5)
    for order in orders:
        if order['status'] == 'closed':
            profit = float(order['info'].get('pnl', 0))
            capital += profit

            result = "WIN" if profit > 0 else "LOSS"
            send_telegram(f"[CLOSE] {result} | PnL: {profit:.2f} USDT\nNew Capital: {capital:.2f} USDT")

            position_open = False
            break

def daily_summary():
    now = datetime.datetime.utcnow()
    if now.hour == 23 and now.minute >= 50:
        balance = capital
        send_telegram(f"[DAILY REPORT]\nCapital: {balance:.2f} USDT\nDate: {now.strftime('%Y-%m-%d')}")

# === MAIN LOOP ===
while True:
    try:
        now = datetime.datetime.utcnow()
        today = now.date()

        if last_trade_date != today:
            trade_count = 0
            last_trade_date = today
            print("[INFO] เริ่มวันใหม่ รีเซ็ตจำนวนไม้เทรดแล้ว")

        if trade_count < DAILY_MAX_TRADES:
            if not position_open:
                direction, entry_price = check_entry()
                if direction:
                    place_order(direction, entry_price)
                    trade_count += 1
            else:
                monitor_position()

        daily_summary()

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"[ERROR] {e}")
        send_telegram(f"[ERROR] {e}")
        time.sleep(10)
