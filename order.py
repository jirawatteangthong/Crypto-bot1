import ccxt
from config import *
from telegram import trade_notify

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

def open_trade(signal, capital):
    direction, price = signal['direction'], signal['price']
    size = round((capital * LEVERAGE) / price, 3)
    side = 'buy' if direction == 'long' else 'sell'

    sl_price = round(signal['sl'], 2)
    tp_price = round(signal['tp'], 2)

    exchange.create_limit_order(SYMBOL, side, size, price)

    exchange.private_post_trade_order_algo({
        'instId': SYMBOL,
        'tdMode': 'cross',
        'side': 'sell' if side == 'buy' else 'buy',
        'ordType': 'oco',
        'sz': size,
        'tpTriggerPx': tp_price,
        'tpOrdPx': '-1',
        'slTriggerPx': sl_price,
        'slOrdPx': '-1'
    })

    trade_notify(direction, price, size, tp_price, sl_price)
    return capital, "pending", False

def monitor_trade():
    # Placeholder: à¸à¸£à¸±à¸ SL à¹à¸¡à¸·à¹à¸­ TP à¸à¸¶à¸ 50%
    pass

def has_open_position():
    positions = exchange.fetch_positions([SYMBOL])
    for pos in positions:
        if float(pos['contracts']) > 0:
            return True
    return False
