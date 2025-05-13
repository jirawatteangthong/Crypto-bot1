from utils import fetch_current_price

def check_entry_signals(fibo, trend_h1):
    price = fetch_current_price()
    entries = []

    if fibo['direction'] == 'long' and fibo['levels']['61.8'] <= price <= fibo['levels']['78.6']:
        entries.append({'direction': 'long', 'price': fibo['levels']['61.8'], 'tp': fibo['tp'], 'sl': fibo['sl'], 'level': '61.8'})
        entries.append({'direction': 'long', 'price': fibo['levels']['78.6'], 'tp': fibo['tp'], 'sl': fibo['sl'], 'level': '78.6'})
    elif fibo['direction'] == 'short' and fibo['levels']['78.6'] <= price <= fibo['levels']['61.8']:
        entries.append({'direction': 'short', 'price': fibo['levels']['61.8'], 'tp': fibo['tp'], 'sl': fibo['sl'], 'level': '61.8'})
        entries.append({'direction': 'short', 'price': fibo['levels']['78.6'], 'tp': fibo['tp'], 'sl': fibo['sl'], 'level': '78.6'})

    return entries
