# === main.py ===
import ccxt
import time
import datetime
from config import *
from telegram import Bot

# INIT
bot = Bot(token=TELEGRAM_TOKEN)
exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

capital = START_CAPITAL
position_open = False
breakeven_moved = False
trade_count = 0
last_trade_date = None
last_zone_alert = None
last_alive_check = time.time()

# === Utility ===
def send_telegram(msg): bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def fetch_price():
    return exchange.fetch_ticker(SYMBOL)['last']

def fetch_ohlcv(tf, limit):
    return exchange.fetch_ohlcv(SYMBOL, timeframe=tf, limit=limit)

# === Fibonacci Zone (H1) ===
def get_fibo_zone():
    h1 = fetch_ohlcv('1h', H1_LIMIT)
    highs = [c[2] for c in h1]
    lows = [c[3] for c in h1]
    swing_high = max(highs)
    swing_low = min(lows)

    zone_top = swing_high - (swing_high - swing_low) * FIBO_ZONE[0]
    zone_bottom = swing_high - (swing_high - swing_low) * FIBO_ZONE[1]
    return zone_bottom, zone_top, swing_high, swing_low

# === MACD Confirm (M5) ===
def macd_confirm():
    m5 = fetch_ohlcv('5m', 50)
    closes = [c[4] for c in m5]
    def ema(val, p):
        k = 2 / (p + 1)
        r = []
        e = val[0]
        for v in val:
            e = v * k + e * (1 - k)
            r.append(e)
        return r
    macd = [a - b for a, b in zip(ema(closes, 12), ema(closes, 26))]
    signal = ema(macd, 9)
    return macd[-2] < signal[-2] and macd[-1] > signal[-1]

# === Entry Check ===
def check_entry_zone():
    global last_zone_alert
    price = fetch_price()
    zone_bottom, zone_top, swing_high, swing_low = get_fibo_zone()
    in_zone = zone_bottom <= price <= zone_top

    if in_zone and last_zone_alert != (zone_bottom, zone_top):
        send_telegram(f"[ZONE] เข้าเขต Fibo Zone H1: {zone_bottom:.2f} - {zone_top:.2f}")
        last_zone_alert = (zone_bottom, zone_top)

    if in_zone and macd_confirm():
        return price, swing_high, swing_low
    return None, None, None

# === Place Order (All-In) ===
def place_order(entry_price, swing_high, swing_low):
    global capital, position_open, breakeven_moved
    size = round((capital * LEVERAGE) / entry_price, 3)
    sl_price = round(swing_high * 1.002, 2)
    tp_price = round(swing_low * 0.995, 2)

    exchange.create_market_order(SYMBOL, 'sell', size)

    exchange.private_post_trade_order_algo({
        'instId': SYMBOL,
        'tdMode': 'cross',
        'side': 'buy',
        'ordType': 'oco',
        'sz': size,
        'tpTriggerPx': tp_price,
        'tpOrdPx': '-1',
        'slTriggerPx': sl_price,
        'slOrdPx': '-1'
    })

    position_open = True
    breakeven_moved = False
    send_telegram(f"[ENTRY] SHORT @ {entry_price}\nSize: {size}\nTP: {tp_price}\nSL: {sl_price}")
    return size, entry_price, tp_price, sl_price

# === Move SL to Breakeven ===
def move_sl_to_breakeven(entry_price, size):
    sl_breakeven = round(entry_price, 2)
    exchange.private_post_trade_order_algo({
        'instId': SYMBOL,
        'tdMode': 'cross',
        'side': 'buy',
        'ordType': 'conditional',
        'sz': size,
        'slTriggerPx': sl_breakeven,
        'slOrdPx': '-1'
    })
    send_telegram(f"[BREAKEVEN] SL เลื่อนเข้า Breakeven @ {sl_breakeven}")

# === Monitor Position ===
def monitor_position(entry_price, tp_price, size):
    global capital, position_open, breakeven_moved

    price = fetch_price()
    midpoint = (entry_price + tp_price) / 2

    # SL to Breakeven
    if not breakeven_moved and price < midpoint:
        move_sl_to_breakeven(entry_price, size)
        breakeven_moved = True

    orders = exchange.fetch_closed_orders(SYMBOL, limit=5)
    for order in orders:
        if order['status'] == 'closed':
            pnl = float(order['info'].get('pnl', 0))
            result = "WIN" if pnl > 0 else "LOSS"
            capital += pnl
            position_open = False
            send_telegram(f"[CLOSE] {result} | PnL: {pnl:.2f} USDT\nNew Capital: {capital:.2f}")
            break

# === Main Loop ===
send_telegram_message("บอทเริ่มทำงานแล้ว [TEST MESSAGE]")

entry_price = None
tp_price = None
size = None

while True:
    try:
        now = datetime.datetime.utcnow()
        today = now.date()

        # Alive message every 5h
        if time.time() - last_alive_check > 18000:
            send_telegram("[ALIVE] บอทยังทำงานอยู่...")
            last_alive_check = time.time()

        if last_trade_date != today:
            trade_count = 0
            last_trade_date = today

        if not position_open and trade_count < DAILY_MAX_TRADES:
            result = check_entry_zone()
            if result[0]:
                entry_price, swing_high, swing_low = result
                size, entry_price, tp_price, sl_price = place_order(entry_price, swing_high, swing_low)
                trade_count += 1

        if position_open:
            monitor_position(entry_price, tp_price, size)

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        send_telegram(f"[ERROR] {e}")
        time.sleep(60)
