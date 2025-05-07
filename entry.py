from utils import fetch_current_price

def check_entries(fibo):
    price = fetch_current_price()
    entries = []

    if fibo['direction'] == 'long' and fibo['levels']['61.8'] <= price <= fibo['levels']['78.6']:
        entries.append({'direction': 'long', 'price': fibo['levels']['61.8'], 'tp': fibo['tp'], 'sl': fibo['sl']})
        entries.append({'direction': 'long', 'price': fibo['levels']['78.6'], 'tp': fibo['tp'], 'sl': fibo['sl']})

    elif fibo['direction'] == 'short' and fibo['levels']['78.6'] <= price <= fibo['levels']['61.8']:
        entries.append({'direction': 'short', 'price': fibo['levels']['61.8'], 'tp': fibo['tp'], 'sl': fibo['sl']})
        entries.append({'direction': 'short', 'price': fibo['levels']['78.6'], 'tp': fibo['tp'], 'sl': fibo['sl']})

    return entries
