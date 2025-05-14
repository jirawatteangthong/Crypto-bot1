# entry.py

from utils import fetch_current_price

def check_entry_signal(fibo, trend):
    price = fetch_current_price()
    level_62 = fibo['levels']['61.8']

    if fibo['direction'] == 'long' and price <= level_62:
        sl = fibo['levels']['100'] - 0.1 * abs(fibo['levels']['0'] - fibo['levels']['100'])
        tp = level_62 + abs(level_62 - sl)
        return {'direction': 'long', 'price': level_62, 'sl': sl, 'tp': tp}

    elif fibo['direction'] == 'short' and price >= level_62:
        sl = fibo['levels']['100'] + 0.1 * abs(fibo['levels']['100'] - fibo['levels']['0'])
        tp = level_62 - abs(sl - level_62)
        return {'direction': 'short', 'price': level_62, 'sl': sl, 'tp': tp}

    return None
