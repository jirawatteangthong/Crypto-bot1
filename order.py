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

open_order_ids = []

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
                # ลบ position ที่เกี่ยวข้องด้วย
                positions = [p for p in positions if p['price'] != o['price']]
        except:
            continue
    return positions, capital
