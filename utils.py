import time
from config import TIMEFRAME
from okx_api import get_ohlcv

daily_summary = []

def is_new_day(current_date):
    return current_date != time.strftime("%Y-%m-%d")

def get_ohlcv():
    return get_ohlcv(timeframe=TIMEFRAME)

def detect_bos(df):
    recent = df.tail(20)
    if recent['high'].iloc[-1] > recent['high'].max():
        return 'uptrend'
    elif recent['low'].iloc[-1] < recent['low'].min():
        return 'downtrend'
    return None

def get_swing_points(df, trend):
    if trend == 'uptrend':
        low = df['low'].min()
        high = df['high'].max()
    else:
        high = df['high'].max()
        low = df['low'].min()
    return high, low

def calculate_fibo_levels(high, low, trend):
    if trend == 'uptrend':
        fib_62 = low + 0.618 * (high - low)
        fib_110 = high + 0.1 * (high - low)
        tp = fib_62 + (fib_110 - fib_62)
    else:
        fib_62 = high - 0.618 * (high - low)
        fib_110 = low - 0.1 * (high - low)
        tp = fib_62 - (fib_62 - fib_110)
    return {'62%': round(fib_62, 2), '110%': round(fib_110, 2), 'tp': round(tp, 2)}

def summarize_daily_trades():
    total_pnl = sum([t['pnl'] for t in daily_summary])
    total_trades = len(daily_summary)
    msg = f"สรุปผลเทรดวันนี้:\nจำนวนไม้: {total_trades}\nรวมกำไร/ขาดทุน: {total_pnl:.2f} USDT"
    from telegram import send_message
    send_message(msg)
    daily_summary.clear()
