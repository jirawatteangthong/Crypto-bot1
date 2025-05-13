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
    side = 'buy' if signal['direction'] == 'long' else 'sell'

    params = {
        'tpTriggerPx': str(signal['tp']),
        'tpOrdPx': '-1',
        'slTriggerPx': str(signal['sl']),
        'slOrdPx': '-1'
    }

    order = exchange.create_order(SYMBOL, 'limit', side, ORDER_SIZE, signal['price'], params)
    trade_notify(direction=signal['direction'], entry=signal['price'],
                 size=ORDER_SIZE, tp=signal['tp'], sl=signal['sl'])
    return capital

def monitor_trades(positions):
    new_positions = []
    capital_change = 0

    for pos in positions:
        try:
            orders = exchange.fetch_open_orders(SYMBOL)
            if not any(abs(o['price'] - pos['price']) < 1e-6 for o in orders):
                pnl = 5  # ใช้ค่านี้แทนกำไรจริง (ควรแก้ให้ดึง PnL จริง)
                result = "WIN" if pnl > 0 else "LOSS"
                trade_notify(result=result, pnl=pnl, new_cap=capital_change + pnl)
                capital_change += pnl
            else:
                new_positions.append(pos)
        except Exception:
            continue

    return new_positions, capital_change

def get_open_positions():
    positions = []
    try:
        orders = exchange.fetch_open_orders(SYMBOL)
        for o in orders:
            pos = {
                'direction': 'long' if o['side'] == 'buy' else 'short',
                'price': o['price'],
                'size': o['amount'],
                'level': 'unknown'
            }
            positions.append(pos)
    except:
        pass
    return positions
