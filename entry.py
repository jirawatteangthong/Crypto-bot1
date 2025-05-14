from utils import exchange
from strategy import fetch_ohlcv, detect_choch
from telegram import alert_price_in_zone
from config import ORDER_SIZE

def check_entry_signal(fibo_data):
    price = exchange.fetch_ticker('BTC-USDT-SWAP')['last']
    lower, upper = fibo_data['entry_zone']
    if lower <= price <= upper:
        alert_price_in_zone()
        m1 = fetch_ohlcv('1m', 30)
        choch = detect_choch(m1)
        if fibo_data['trend'] == 'long' and choch == 'bullish':
            return {'direction': 'long', 'size': ORDER_SIZE, 'tp': fibo_data['tp'], 'sl': fibo_data['sl']}
        elif fibo_data['trend'] == 'short' and choch == 'bearish':
            return {'direction': 'short', 'size': ORDER_SIZE, 'tp': fibo_data['tp'], 'sl': fibo_data['sl']}
    return None
