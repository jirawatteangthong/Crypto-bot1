from utils import fetch_current_price

def check_entry_signal(fibo, trend):
    price = fetch_current_price()
    if fibo['direction'] == 'long' and price <= fibo['price']:
        return fibo
    elif fibo['direction'] == 'short' and price >= fibo['price']:
        return fibo
    return None
