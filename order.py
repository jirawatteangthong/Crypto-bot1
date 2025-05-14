from telegram import send_message

current_order = None

def open_trade(exchange, direction, entry_price, sl_price, tp_price):
    global current_order
    if current_order:
        return

    side = 'buy' if direction == 'long' else 'sell'

    params = {
        'stopLoss': {'price': sl_price},
        'takeProfit': {'price': tp_price}
    }

    order = exchange.create_market_order(SYMBOL, side, ORDER_SIZE, params=params)
    current_order = order

    send_message(f"เปิดออเดอร์ {direction.upper()} ที่ {entry_price}\nSL: {sl_price}, TP: {tp_price}")

def close_trade(exchange):
    global current_order
    if not current_order:
        return

    exchange.cancel_order(current_order['id'], SYMBOL)
    send_message("ปิดออเดอร์")
    current_order = None
