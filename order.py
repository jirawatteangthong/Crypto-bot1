from okx_api import place_order, get_open_orders, cancel_all_orders
from telegram import send_message

active_trade = None

def check_open_orders():
    global active_trade
    return active_trade is not None

def open_trade(signal):
    global active_trade
    side = 'buy' if signal['side'] == 'buy' else 'sell'
    result = place_order(
        side=side,
        price=signal['entry'],
        sl=signal['sl'],
        tp=signal['tp']
    )
    if result:
        active_trade = result
        send_message(f"เปิดออเดอร์ {side.upper()} ที่ {signal['entry']}, TP: {signal['tp']}, SL: {signal['sl']}")

def update_trade_status():
    global active_trade
    order_status = get_open_orders()
    if not order_status:
        # สมมุติว่าปิดแล้ว
        pnl = active_trade.get("pnl", 0)
        send_message(f"ปิดออเดอร์ กำไร/ขาดทุน: {pnl} USDT")
        active_trade = None
