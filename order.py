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
    opposite_side = 'sell' if side == 'buy' else 'buy'

    tp = signal['tp']
    sl = signal['sl']
    price = signal['price']

    # สร้างออเดอร์เข้า พร้อมตั้ง TP / SL ด้วย OCO
    params = {
        'tdMode': 'cross',
        'posSide': 'long' if side == 'buy' else 'short',
        'ordType': 'oco',
        'tpTriggerPx': str(tp),
        'tpOrdPx': str(tp),
        'slTriggerPx': str(sl),
        'slOrdPx': str(sl)
    }

    order = exchange.create_order(
        symbol=SYMBOL,
        type='limit',
        side=side,
        amount=ORDER_SIZE,
        price=price,
        params=params
    )

    trade_notify(direction=signal['direction'], entry=price,
                 size=ORDER_SIZE, tp=tp, sl=sl)

    return capital

def get_open_positions():
    positions = exchange.fetch_positions([SYMBOL])
    result = []
    for pos in positions:
        if float(pos['contracts']) > 0:
            direction = 'long' if pos['side'] == 'long' else 'short'
            result.append({
                'direction': direction,
                'price': float(pos['entryPrice']),
                'size': float(pos['contracts']),
                'level': None  # ยังไม่มีข้อมูล level
            })
    return result

def monitor_trades(positions, capital):
    new_positions = []
    delta = 0

    for pos in positions:
        pos_side = 'long' if pos['direction'] == 'long' else 'short'
        all_positions = exchange.fetch_positions([SYMBOL])
        active = any(float(p['contracts']) > 0 and p['side'] == pos_side for p in all_positions)

        if not active:
            # ปิดแล้ว คำนวณกำไรขาดทุน
            closed = exchange.fetch_my_trades(SYMBOL, limit=5)
            for t in closed[::-1]:
                if (t['side'] == pos['direction']) and (abs(t['amount'] - ORDER_SIZE) < 1e-3):
                    pnl = float(t.get('info', {}).get('pnl', 0))
                    capital += pnl
                    delta += pnl
                    trade_notify(result="WIN" if pnl > 0 else "LOSS", pnl=pnl, new_cap=capital)
                    break
        else:
            new_positions.append(pos)

    return new_positions, delta
