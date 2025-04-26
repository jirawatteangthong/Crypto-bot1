# main.py
import ccxt
import time
import requests
import csv
from statistics import mean, stdev
from datetime import datetime, timezone

# === CONFIG ===
API_KEY = '0659b6f2-c86a-466a-82ec-f1a52979bc33'
API_SECRET = 'CCB0A67D53315671F599050FCD712CD1'
API_PASSPHRASE = 'Jirawat1-'

SYMBOL = 'BTC-USDT-SWAP'
LEVERAGE = 20
BASE_CAPITAL = 20
WITHDRAW_THRESHOLD = 3

TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

# === STATE ===
capital = BASE_CAPITAL
win_count = 0
loss_count = 0
position_open = False

# daily summary state
daily_win = 0
daily_loss = 0
daily_pnl = 0.0
last_summary_date = datetime.now(timezone.utc).date()

# === EXCHANGE & TELEGRAM ===
okx = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'},
})

def telegram(msg):
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        print("[Telegram]", r.status_code, r.text)
    except Exception as e:
        print("[Telegram Error]", e)

# === UTILITIES ===
def get_ohlcv_safe(symbol, tf, limit=50, retries=5):
    for _ in range(retries):
        try:
            data = okx.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
            if data and len(data) >= limit:
                return data
        except:
            time.sleep(1)
    raise Exception(f"fetch_ohlcv failed: {tf}")

def calculate_macd(data, fast=12, slow=26, signal=9):
    def ema(vals, per):
        k = 2/(per+1); e = vals[0]; out = []
        for v in vals:
            e = v*k + e*(1-k)
            out.append(e)
        return out
    macd_line = [f-s for f,s in zip(ema(data, fast), ema(data, slow))]
    sig_line = ema(macd_line, signal)
    hist = [m-s for m,s in zip(macd_line, sig_line)]
    return macd_line, sig_line, hist

def set_leverage():
    try:
        okx.set_leverage(LEVERAGE, SYMBOL, {'marginMode':'cross'})
    except:
        pass

# === ENTRY LOGIC ===
def check_entry():
    # trend on M30
    m30 = get_ohlcv_safe(SYMBOL, '30m')
    m30_close = [c[4] for c in m30]
    trend_up = m30_close[-1] > m30_close[-2] > m30_close[-3]

    # swing on M15
    m15 = get_ohlcv_safe(SYMBOL, '15m')
    highs = [c[2] for c in m15[-10:]]; lows = [c[3] for c in m15[-10:]]
    swing_high, swing_low = max(highs), min(lows)

    # MACD on M1
    m1 = get_ohlcv_safe(SYMBOL, '1m')
    closes = [c[4] for c in m1]
    macd, sig, _ = calculate_macd(closes)
    cross_up = macd[-2]<sig[-2] and macd[-1]>sig[-1]
    cross_dn = macd[-2]>sig[-2] and macd[-1]<sig[-1]
    price = closes[-1]

    if trend_up and cross_up and price <= swing_low:
        return "long", price, swing_low, swing_high
    if not trend_up and cross_dn and price >= swing_high:
        return "short", price, swing_low, swing_high
    return None, None, None, None

# === ORDER & OCO ===
def place_order(direction, entry, sl, tp):
    size = round((capital * LEVERAGE) / entry, 3)
    side = 'buy' if direction=='long' else 'sell'
    sl_side = 'sell' if side=='buy' else 'buy'
    # market entry
    okx.create_market_order(SYMBOL, side, size)
    telegram(f"[ENTRY] {direction}@{entry} SL:{sl} TP:{tp} Size:{size}")
    # OCO
    okx.private_post_trade_order_algo({
        'instId':SYMBOL,'tdMode':'cross',
        'side': sl_side,'ordType':'oco','sz':size,
        'tpTriggerPx': tp,'tpOrdPx':'-1',
        'slTriggerPx': sl,'slOrdPx':'-1'
    })
    return size

# === DAILY SUMMARY ===
def try_daily_summary():
    global last_summary_date, daily_win, daily_loss, daily_pnl
    today = datetime.now(timezone.utc).date()
    if today != last_summary_date:
        # send summary for last_summary_date
        msg = (
            f"[สรุปรายวัน {last_summary_date}]\n"
            f"Win: {daily_win} | Loss: {daily_loss}\n"
            f"Net PnL: {round(daily_pnl,2)} USDT\n"
            f"Capital: {round(capital,2)} USDT"
        )
        telegram(msg)
        # reset counters
        daily_win = daily_loss = 0
        daily_pnl = 0.0
        last_summary_date = today

# === MAIN LOOP ===
def main_loop():
    global position_open, capital, win_count, loss_count, daily_win, daily_loss, daily_pnl

    telegram("บอทพี่ทำงานแล้ว")
    set_leverage()

    sl_moved = False
    entry = sl = tp = size = None
    direction = None

    while True:
        try:
            try_daily_summary()

            if not position_open:
                direction, entry, swing_low, swing_high = check_entry()
                if direction:
                    # define SL/TP from swings
                    if direction=='long':
                        sl = swing_low
                        tp = entry + (entry - swing_low)
                    else:
                        sl = swing_high
                        tp = entry - (swing_high - entry)
                    size = place_order(direction, entry, sl, tp)
                    position_open = True
                    sl_moved = False

            else:
                ticker = okx.fetch_ticker(SYMBOL)
                price = ticker['last']

                # move SL to breakeven at half TP
                half_tp = (entry+tp)/2 if direction=='long' else (entry+tp)/2
                if not sl_moved and ((direction=='long' and price>=half_tp) or (direction=='short' and price<=half_tp)):
                    # cancel existing OCO
                    okx.cancel_all_orders(SYMBOL)
                    # new OCO breakeven
                    sl_breakeven = entry
                    okx.private_post_trade_order_algo({
                        'instId':SYMBOL,'tdMode':'cross',
                        'side': 'sell' if direction=='long' else 'buy',
                        'ordType':'oco','sz':size,
                        'tpTriggerPx': tp,'tpOrdPx':'-1',
                        'slTriggerPx': sl_breakeven,'slOrdPx':'-1'
                    })
                    telegram(f"[SL MOVE] Breakeven @ {entry}")
                    sl_moved = True

                # check TP / SL hit
                if (direction=='long' and price>=tp) or (direction=='short' and price<=tp):
                    profit = (tp-entry)*size if direction=='long' else (entry-tp)*size
                    capital += profit; win_count += 1; daily_win += 1; daily_pnl += profit
                    telegram(f"[TP HIT] +{round(profit,2)} USDT | Capital: {round(capital,2)}")
                    position_open = False

                    # withdraw every N wins
                    if win_count % WITHDRAW_THRESHOLD == 0:
                        w = capital/2; capital -= w
                        telegram(f"[WITHDRAW] {round(w,2)} USDT | Remain: {round(capital,2)}")

                elif (direction=='long' and price<=sl) or (direction=='short' and price>=sl):
                    loss = (entry-sl)*size if direction=='long' else (sl-entry)*size
                    capital -= abs(loss); loss_count +=1; daily_loss+=1; daily_pnl -= abs(loss)
                    telegram(f"[SL HIT] -{round(abs(loss),2)} USDT | Capital: {round(capital,2)}")
                    position_open = False

        except Exception as e:
            telegram(f"[ERROR] {e}")

        time.sleep(5)


if __name__ == '__main__':
    main_loop()
