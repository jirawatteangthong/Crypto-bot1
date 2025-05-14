import ccxt
from config import *
from telegram import trade_notify
from utils import fetch_current_price

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
        'tpTriggerPx': signal['tp'],
        'tpOrdPx': signal['tp'],
        'slTriggerPx': signal['sl'],
        'slOrdPx': signal['sl']
    }

    order = exchange.create_limit_order(SYMBOL, side, ORDER_SIZE, signal['price'], params)
    trade_notify(direction=signal['direction'], entry=signal['price'],
                 size=ORDER_SIZE, tp=signal['tp'], sl=signal['sl'])
    return capital

def monitor_trades(positions, capital):
    active_positions = []
    for pos in positions:
        try:
            price_now = fetch_current_price()
            pnl = (price_now - pos['price']) * ORDER_SIZE * LEVERAGE
            pnl = pnl if pos['direction'] == 'long' else -pnl

            tp_half = (pos['tp'] + pos['price']) / 2 if pos['direction'] == 'long' else (pos['price'] + pos['tp']) / 2
            if not pos.get('sl_moved') and (
                (pos['direction'] == 'long' and price_now >= tp_half) or
                (pos['direction'] == 'short' and price_now <= tp_half)
            ):
                exchange.create_order(SYMBOL, 'market', 'sell' if pos['direction'] == 'long' else 'buy', 0, None, {
                    'slTriggerPx': pos['price'],
                    'slOrdPx': pos['price']
                })
                pos['sl_moved'] = True

            orders = exchange.fetch_open_orders(SYMBOL)
            filled = all(abs(o['price'] - pos['price']) > 1e-5 for o in orders)
            if filled:
                capital += pnl
                result = "WIN" if pnl > 0 else "LOSS"
                trade_notify(result=result, pnl=pnl, new_cap=capital)
            else:
                active_positions.append(pos)
        except:
            continue
    return active_positions, capital

def get_open_positions():
    try:
        orders = exchange.fetch_open_orders(SYMBOL)
        positions = []
        for o in orders:
            positions.append({
                'direction': 'long' if o['side'] == 'buy' else 'short',
                'price': float(o['price']),
                'size': float(o['amount']),
                'level': o['info'].get('tag', 'manual')
            })
        return positions
    except:
        return []
