from utils import fetch_current_price

def check_entries(fibo):
    price = fetch_current_price()
    entries = []

    if fibo['trend'] == 'bullish' and fibo['61.8'] <= price <= fibo['78.6']:
        entries.append({'direction': 'long', 'price': fibo['61.8'], 'tp': fibo['tp'], 'sl': fibo['sl']})
        entries.append({'direction': 'long', 'price': fibo['78.6'], 'tp': fibo['tp'], 'sl': fibo['sl']})
    elif fibo['trend'] == 'bearish' and fibo['78.6'] <= price <= fibo['61.8']:
        entries.append({'direction': 'short', 'price': fibo['61.8'], 'tp': fibo['tp'], 'sl': fibo['sl']})
        entries.append({'direction': 'short', 'price': fibo['78.6'], 'tp': fibo['tp'], 'sl': fibo['sl']})

    return entries
