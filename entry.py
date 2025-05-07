from utils import fetch_current_price

def check_entry_signals(fibo, trend):
    price = fetch_current_price()
    entries = []
    levels = fibo['levels']

    if fibo['direction'] == 'long' and levels['61.8'] <= price <= levels['78.6']:
        for lvl in ['61.8', '78.6']:
            entries.append({'direction': 'long', 'price': levels[lvl], 'tp': fibo['tp'], 'sl': fibo['sl'], 'level': lvl})

    elif fibo['direction'] == 'short' and levels['78.6'] <= price <= levels['61.8']:
        for lvl in ['61.8', '78.6']:
            entries.append({'direction': 'short', 'price': levels[lvl], 'tp': fibo['tp'], 'sl': fibo['sl'], 'level': lvl})

    return entries
