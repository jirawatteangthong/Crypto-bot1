import ccxt
import time, datetime
from config import *
from telegram import Bot

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

bot = Bot(token=TELEGRAM_TOKEN)

# ตัวแปรหลัก
capital = START_CAPITAL
trade_count = 0
last_trade_date = None
position_open = False
entry_price = 0
tp_price = 0
sl_price = 0
win_streak = 0
last_notify_time = None

# === MACD
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

def send_telegram(msg):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
def get_price():
    return exchange.fetch_ticker(SYMBOL)['last']

def get_m15_structure():
    candles = exchange.fetch_ohlcv(SYMBOL, timeframe='15m', limit=50)
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    return max(highs), min(lows)

def check_entry():
    candles = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=50)
    closes = [c[4] for c in candles]
    macd, signal, _ = calculate_macd(closes)
    cross_up = macd[-2] < signal[-2] and macd[-1] > signal[-1]
    cross_down = macd[-2] > signal[-2] and macd[-1] < signal[-1]
    
    h1_candles = exchange.fetch_ohlcv(SYMBOL, '1h', limit=50)
    h1_close = h1_candles[-1][4]
    h1_open = h1_candles[-1][1]
    trend_up = h1_close > h1_open

    if trend_up and cross_up:
        return 'long'
    elif not trend_up and cross_down:
        return 'short'
    else:
        return None
def place_order(direction):
    global capital, position_open, entry_price, tp_price, sl_price

    entry_price = get_price()
    size = round((capital * LEVERAGE) / entry_price, 3)
    side = 'buy' if direction == 'long' else 'sell'
    sl_side = 'sell' if side == 'buy' else 'buy'

    high, low = get_m15_structure()
    sl_price = round(low * 0.999 if direction == 'long' else high * 1.001, 2)
    tp_price = round(entry_price * 1.02 if direction == 'long' else entry_price * 0.98, 2)

    exchange.create_market_order(SYMBOL, side, size)
    send_telegram(f"[ENTRY] {direction.upper()} @ {entry_price}\nTP: {tp_price}, SL: {sl_price}")
    position_open = True
def monitor_trade():
    global position_open, capital, trade_count, win_streak

    current_price = get_price()
    if position_open:
        profit_zone = abs(current_price - entry_price) >= abs(tp_price - entry_price) * 0.5
        if profit_zone:
            sl_price = entry_price
            send_telegram("[SL MOVE] SL moved to breakeven!")

        if (tp_price and current_price >= tp_price) or (sl_price and current_price <= sl_price):
            result = "WIN" if current_price >= tp_price else "LOSS"
            gain = abs(capital * 0.02) if result == "WIN" else -abs(capital * 0.01)
            capital += gain
            position_open = False
            win_streak = win_streak + 1 if result == "WIN" else 0
            trade_count += 1
            send_telegram(f"[CLOSE] {result} | PnL: {gain:.2f} USDT\nNew Capital: {capital:.2f}")

            if win_streak >= 3:
                withdraw_profit()
                win_streak = 0
def withdraw_profit():
    send_telegram("[WITHDRAW] Bot withdraws partial profit.")

def heartbeat():
    global last_notify_time
    now = datetime.datetime.utcnow()
    if not last_notify_time or (now - last_notify_time).total_seconds() > 18000:
        send_telegram("[STATUS] Bot is alive.")
        last_notify_time = now

send_telegram("[START] Bot started.")

while True:
    try:
        now = datetime.datetime.utcnow().date()
        if last_trade_date != now:
            trade_count = 0
            last_trade_date = now

        if not position_open and trade_count < DAILY_MAX_TRADES:
            signal = check_entry()
            if signal:
                place_order(signal)

        monitor_trade()
        heartbeat()
        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        send_telegram(f"[ERROR] {str(e)}")
        time.sleep(10)
