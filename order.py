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

    # คำนวณ TP/SL ที่ Fibo 10 และ 110/120
    tp_price = signal['tp']
    sl_price = signal['sl']

    # เปิดออเดอร์พร้อม TP/SL ด้วย OCO
    params = {
        'tpTriggerPx': tp_price,
        'tpOrdPx': tp_price,
        'slTriggerPx': sl_price,
        'slOrdPx': sl_price
    }

    order = exchange.create_limit_order(SYMBOL, side, ORDER_SIZE, signal['price'], params)
    trade_notify(direction=signal['direction'], entry=signal['price'],
                 size=ORDER_SIZE, tp=tp_price, sl=sl_price)
    return capital

def monitor_trades(positions, capital):
    active_positions = []
    for pos in positions:
        try:
            side = 'buy' if pos['direction'] == 'long' else 'sell'
            open_orders = exchange.fetch_open_orders(SYMBOL)
            filled = True
            for o in open_orders:
                if abs(o['price'] - pos['price']) < 1e-5 and o['side'] == side:
                    filled = False
                    break
            if filled:
                price_now = fetch_current_price()
                pnl = (price_now - pos['price']) * ORDER_SIZE * LEVERAGE
                pnl = pnl if pos['direction'] == 'long' else -pnl
                capital += pnl
                result = "WIN" if pnl > 0 else "LOSS"
                trade_notify(result=result, pnl=pnl, new_cap=capital)
            else:
                active_positions.append(pos)
        except Exception as e:
            continue
    return active_positions, capital

def get_open_positions():
    try:
        orders = exchange.fetch_open_orders(SYMBOL)
        positions = []
        for o in orders:
            pos = {
                'direction': 'long' if o['side'] == 'buy' else 'short',
                'price': float(o['price']),
                'size': float(o['amount']),
                'level': '61.8' if '61.8' in o['info'].get('tag', '') else '78.6'
            }
            positions.append(pos)
        return positions
    except:
        return []
