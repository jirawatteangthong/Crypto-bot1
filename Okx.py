import ccxt
from config import API_KEY, API_SECRET, API_PASSPHRASE, SYMBOL, ORDER_SIZE

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

def get_ohlcv(symbol=SYMBOL, timeframe='5m', limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except:
        return None

def place_order(side, price, sl, tp):
    # Simplified market order with TP/SL via bot logic
    try:
        order = exchange.create_order(
            symbol=SYMBOL,
            type='market',
            side=side,
            amount=ORDER_SIZE
        )
        return {'id': order['id'], 'side': side, 'entry': price, 'tp': tp, 'sl': sl}
    except Exception as e:
        print(f"Order Error: {e}")
        return None

def get_open_orders():
    try:
        orders = exchange.fetch_open_orders(SYMBOL)
        return orders
    except:
        return []
