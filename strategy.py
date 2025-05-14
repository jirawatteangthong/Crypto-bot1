from utils import fetch_ohlcv, detect_bos, fetch_current_price

prev_fibo = None

def get_fibo_zone():
    global prev_fibo

    m5 = fetch_ohlcv('5m')[-50:]
    trend = detect_bos(m5)
    if not trend:
        return None, None, 'wait'

    highs = [c[2] for c in m5[-20:]]
    lows = [c[3] for c in m5[-20:]]
    high = max(highs)
    low = min(lows)

    price = fetch_current_price()
    if trend == 'bullish':
        entry = low + 0.62 * (high - low)
        sl = high + 0.1 * (high - low)
        tp = entry + (sl - entry)
        fibo = {'direction': 'long', 'price': entry, 'tp': tp, 'sl': sl}
    else:
        entry = high - 0.62 * (high - low)
        sl = low - 0.1 * (high - low)
        tp = entry - (entry - sl)
        fibo = {'direction': 'short', 'price': entry, 'tp': tp, 'sl': sl}

    return fibo, trend, 'ok'
