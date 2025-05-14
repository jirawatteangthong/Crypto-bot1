from utils import fetch_current_price, fetch_ohlcv, detect_choch

def check_entry_signal(fibo):
    price = fetch_current_price()
    if fibo['direction'] == 'long' and fibo['levels']['78.6'] <= price <= fibo['levels']['61.8']:
        m1 = fetch_ohlcv('1m')
        if detect_choch(m1) == 'bullish':
            return {
                'direction': 'long',
                'price': price,
                'tp': fibo['levels']['10.0'],
                'sl': fibo['levels']['110.0'],
                'level': 'm1-confirmed'
            }
    elif fibo['direction'] == 'short' and fibo['levels']['61.8'] <= price <= fibo['levels']['78.6']:
        m1 = fetch_ohlcv('1m')
        if detect_choch(m1) == 'bearish':
            return {
                'direction': 'short',
                'price': price,
                'tp': fibo['levels']['10.0'],
                'sl': fibo['levels']['110.0'],
                'level': 'm1-confirmed'
            }
    return None
