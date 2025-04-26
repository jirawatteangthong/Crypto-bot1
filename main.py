# === main.py ===
import ccxt
import requests
import time
import datetime
from config import *
from telegram import Bot
import config

# ตัวแปรสำหรับจำกัดจำนวนเทรดต่อวัน
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

# ตัวแปรสำหรับนับจำนวนไม้
daily_trade_count = 0
total_trades = 0

# โหลด EMA สำหรับเทรนด์
def fetch_ema():
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=EMA_TF, limit=EMA_PERIOD + 1)
    closes = [bar[4] for bar in bars]
    ema = sum(closes[-EMA_PERIOD:]) / EMA_PERIOD
    return ema

# ดึงราคาปัจจุบัน
def fetch_price():
    ticker = exchange.fetch_ticker(SYMBOL)
    return ticker['last']

# ส่งข้อความไป Telegram
def send_telegram(message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    # === STRATEGY CONFIG ===
EMA_TF = '1h'       # ใช้ H1 ดูเทรนด์หลัก
EMA_PERIOD = 50     # EMA 50
ENTRY_TF = '15m'    # ใช้ M15 เข้าจุด
MICRO_TF = '1m'     # ใช้ M1 Confirm

LEVERAGE = 15
START_CAPITAL = 20
DAILY_MAX_TRADES = 1

# ตัวแปรทุน
capital = START_CAPITAL
position_open = False
today = datetime.datetime.utcnow().date()

# === MACD CALCULATION ===
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
    # === CHECK ENTRY ===
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
        # === PLACE ORDER ===
def place_order(direction, price):
    global capital, position_open

    size = round((capital * LEVERAGE) / price, 3)
    side = 'buy' if direction == "long" else 'sell'
    sl_side = 'sell' if side == 'buy' else 'buy'

    sl_price = round(price * (0.995 if direction == "long" else 1.005), 2)
    tp_price = round(price * (1.01 if direction == "long" else 0.99), 2)

    # Place Market Order
    exchange.create_market_order(SYMBOL, side, size)
    
    # Place OCO TP/SL
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
    # === MONITOR POSITION ===
def monitor_position():
    global capital, position_open

    orders = exchange.fetch_orders(SYMBOL, limit=5)
    for order in orders:
        if order['status'] == 'closed':
            profit = order['info'].get('pnl', 0)
            capital += float(profit)

            result = "WIN" if float(profit) > 0 else "LOSS"
            send_telegram(f"[CLOSE] {result} | PnL: {profit:.2f} USDT\nNew Capital: {capital:.2f} USDT")

            position_open = False
            break
            # === DAILY SUMMARY ===
def daily_summary():
    now = datetime.datetime.utcnow()
    if now.hour == 23 and now.minute >= 50:  # ส่งตอนเที่ยงคืน UTC ใกล้ ๆ
        balance = capital
        send_telegram(f"[DAILY REPORT]\nCapital: {balance:.2f} USDT\nDate: {now.strftime('%Y-%m-%d')}")
        # === MAIN LOOP ===
while True:
    try:
        now = datetime.datetime.utcnow()
        today = now.date()

        # ถ้าเปลี่ยนวัน รีเซ็ต trade_count
        if last_trade_date != today:
            trade_count = 0
            last_trade_date = today
            print("[INFO] เริ่มวันใหม่ รีเซ็ตจำนวนไม้เทรดแล้ว")

        # เช็กจำนวนไม้ที่เทรดไปในวันนี้
        if trade_count < config.DAILY_MAX_TRADES:
            # เงื่อนไขของกลยุทธ์คุณ เช่น TF, EMA, SMC ฯลฯ
            should_open_trade = check_strategy_conditions()

            if should_open_trade:
                open_position()  # สมมุติว่าเป็นฟังก์ชันเปิดออเดอร์จริง
                trade_count += 1

                # ส่งข้อความแจ้งเตือน Telegram ว่าเปิดออเดอร์
                send_telegram_message(f"เปิดออเดอร์ใหม่! วันนี้เทรดไปแล้ว {trade_count} ไม้")
        else:
            print("[INFO] วันนี้ครบจำนวนไม้ที่กำหนดแล้ว")

        time.sleep(config.CHECK_INTERVAL)

    except Exception as e:
        print(f"[ERROR] {e}")
        send_telegram_message(f"[ERROR] เกิดข้อผิดพลาด: {e}")
        time.sleep(10)
