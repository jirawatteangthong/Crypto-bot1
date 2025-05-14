from utils import fetch_current_price, fetch_ohlcv, detect_choch
from telegram import alert_price_in_zone

def check_entry_signal(fibo):
    price = fetch_current_price()
    in_zone = fibo['levels']['61.8'] <= price <= fibo['levels']['78.6'] if fibo['direction'] == 'long' else fibo['levels']['78.6'] <= price <= fibo['levels']['61.8']
    if not in_zone:
        return None

    alert_price_in_zone()

    m1 = fetch_ohlcv('1m')[-50:]
    m1_choch = detect_choch(m1)
    if (fibo['direction'] == 'long' and m1_choch == 'bullish') or (fibo['direction'] == 'short' and m1_choch == 'bearish'):
        return {
            'direction': fibo['direction'],
            'price': price,
            'tp': fibo['tp'],
            'sl': fibo['sl'],
            'size': 0.7
        }
    return None
