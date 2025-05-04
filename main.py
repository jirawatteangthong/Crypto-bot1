import ccxt
import time
import datetime
from config import *
from telegram import Bot

# --- INIT ---
exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
bot = Bot(token=TELEGRAM_TOKEN)

trade_count = 0
last_trade_date = None
capital = START_CAPITAL
position_open = False
last_ping_time = None
win_streak = 0

def send_telegram(msg):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

# --- INDICATOR CALCULATION ---
def fetch_ema():
    candles = exchange.fetch_ohlcv(SYMBOL, timeframe='1h', limit=EMA_PERIOD + 1)
    closes = [c[4] for c in candles]
    return sum(closes[-EMA_PERIOD:]) / EMA_PERIOD

def fetch_price():
    return exchange.fetch_ticker(SYMBOL)['last']

def calculate_macd(closes, fast=12, slow=26, signal=9):
    def ema(vals, period):
        k = 2 / (period + 1)
        result = []
        ema_prev = vals[0]
        for val in vals:
            ema_now = val * k + ema_prev * (1 - k)
            result.append(ema_now)
            ema_prev = ema_now
        return result

    macd_line = [f - s for f, s in zip(ema(closes, fast), ema(closes, slow))]
    signal_line = ema(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, hist

# --- STRATEGY CHECK ---
def check_entry():
    ema = fetch_ema()
    price = fetch_price()

    trend_up = price > ema

    m1_data = exchange.fetch_ohlcv(SYMBOL, '1m', limit=50)
    closes = [x[4] for x in m1_data]
    macd, signal, hist = calculate_macd(closes)

    cross_up = macd[-2] < signal[-2] and macd[-1] > signal[-1]
    cross_down = macd[-2] > signal[-2] and macd[-1] < signal[-1]

    if trend_up and cross_up:
        return "long", price
    elif not trend_up and cross_down:
        return "short", price
    return None, None

# --- ORDER LOGIC ---
def place_order(direction, entry_price):
    global capital, position_open

    size = round((capital * LEVERAGE) / entry_price, 3)
    side = 'buy' if direction == "long" else 'sell'
    sl_side = 'sell' if side == 'buy' else 'buy'
    tp = round(entry_price * (1.01 if direction == 'long' else 0.99), 2)
    sl = round(entry_price * (0.995 if direction == 'long' else 1.005), 2)

    exchange.create_market_order(SYMBOL, side, size)

    exchange.private_post_trade_order_algo({
        'instId': SYMBOL,
        'tdMode': 'cross',
        'side': sl_side,
        'ordType': 'oco',
        'sz': size,
        'tpTriggerPx': tp,
        'tpOrdPx': '-1',
        'slTriggerPx': sl,
        'slOrdPx': '-1'
    })

    position_open = True
    send_telegram(f"[ENTRY] {direction.upper()} @ {entry_price}\nTP: {tp} | SL: {sl}\nSize: {size}")

# --- MONITOR PNL ---
def check_closed_orders():
    global position_open, capital, trade_count, win_streak

    closed_orders = exchange.fetch_closed_orders(SYMBOL, limit=5)
    for o in closed_orders:
        if o['status'] == 'closed' and float(o['info'].get('pnl', 0)) != 0:
            pnl = float(o['info'].get('pnl', 0))
            capital += pnl
            result = "WIN" if pnl > 0 else "LOSS"
            win_streak = win_streak + 1 if pnl > 0 else 0
            send_telegram(f"[CLOSE] {result} | PnL: {pnl:.2f} USDT\nCapital: {capital:.2f}")
            trade_count += 1
            position_open = False

            # ถอนทุนเมื่อชนะครบ 3 ไม้ติด
            if win_streak >= 3:
                withdraw_profit = capital * 0.5
                capital -= withdraw_profit
                send_telegram(f"[WITHDRAW] กำไรสะสมครบ 3 ไม้ติด\nถอนทุน: {withdraw_profit:.2f} USDT\nทุนใหม่: {capital:.2f}")
                win_streak = 0
            break

# --- PING EVERY 5 HOURS ---
def ping_status():
    global last_ping_time
    now = datetime.datetime.utcnow()
    if not last_ping_time or (now - last_ping_time).seconds >= 18000:
        send_telegram(f"[PING] Bot is running... Capital: {capital:.2f} USDT\n{now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        last_ping_time = now

# --- DAILY SUMMARY ---
def daily_summary():
    now = datetime.datetime.utcnow()
    if now.hour == 23 and now.minute >= 55:
        send_telegram(f"[DAILY SUMMARY] Capital: {capital:.2f} USDT\nDate: {now.strftime('%Y-%m-%d')}")

# --- MAIN LOOP ---
send_telegram("[BOT STARTED] ระบบเริ่มทำงานแล้ว")
while True:
    try:
        now = datetime.datetime.utcnow()
        today = now.date()
        ping_status()

        if last_trade_date != today:
            trade_count = 0
            last_trade_date = today

        if not position_open and trade_count < DAILY_MAX_TRADES:
            direction, price = check_entry()
            if direction:
                place_order(direction, price)

        if position_open:
            check_closed_orders()

        daily_summary()
        time.sleep(60)

    except Exception as e:
        send_telegram(f"[ERROR] {e}")
        time.sleep(30)
