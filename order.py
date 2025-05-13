import ccxt
from config import *
from telegram import trade_notify

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'futures'}
})

open_order_ids = []

def open_trade(signal, capital):
    side = 'buy' if signal['direction'] == 'long' else 'sell'
    tp = signal['tp']
    sl = signal['sl']
    price = signal['price']

    # สร้าง order พร้อม stop-loss และ take-profit
    params = {
        'tdMode': 'isolated',
        'slTriggerPx': sl,
        'slOrdPx': sl,
        'tpTriggerPx': tp,
        'tpOrdPx': tp
    }

    order = exchange.create_limit_order(
        symbol=SYMBOL,
        side=side,
        amount=ORDER_SIZE,
        price=price,
        params=params
    )

    open_order_ids.append(order['id'])

    trade_notify(direction=signal['direction'], entry=price,
                 size=ORDER_SIZE, tp=tp, sl=sl)
    return capital


def monitor_trades(positions, capital):
    global open_order_ids
    for order_id in open_order_ids[:]:
        try:
            o = exchange.fetch_order(order_id, SYMBOL)
            if o['status'] == 'closed':
                pnl = float(o['info'].get('pnl', 0))
                result = "WIN" if pnl > 0 else "LOSS"
                capital += pnl
                trade_notify(result=result, pnl=pnl, new_cap=capital)
                open_order_ids.remove(order_id)
                # ลบ position ที่เกี่ยวข้อง
                positions = [p for p in positions if p['price'] != o['price']]
        except Exception as e:
            print(f"[monitor_trades ERROR] {str(e)}")
            continue
    return positions, capital


def get_open_positions():
    try:
        positions = exchange.fetch_positions([SYMBOL])
        open_positions = []
        for pos in positions:
            if float(pos['contracts']) > 0:
                open_positions.append({
                    'direction': 'long' if pos['side'] == 'long' else 'short',
                    'price': float(pos['entryPrice']),
                    'size': float(pos['contracts']),
                    'unrealizedPnl': float(pos['unrealizedPnl'])
                })
        return open_positions
    except Exception as e:
        print(f"[get_open_positions ERROR] {str(e)}")
        return []
