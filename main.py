import time
from config import CHECK_INTERVAL, START_CAPITAL
from strategy import get_fibo_zone
from entry import check_entry_signals
from order import open_position, close_position, check_and_update_sl, open_order
from telegram import trade_notify, health_check

capital = START_CAPITAL
last_health_check = 0

notify("[BOT STARTED] ✅บอทเริ่มทำงานแล้ว💰")
positions = get_open_positions()

while True:
    try:
        fibo, trend, status = get_fibo_zone()

        if status == 'ok' and not open_order:
            entries = check_entry_signals(fibo)
            if entries:
                # ใช้เฉพาะไม้เดียว M1 (ไม้แรกจาก M1 ที่เข้าเงื่อนไข)
                entry = entries[0]
                open_order_data = open_position(entry['price'], entry['direction'], entry['tp'], entry['sl'])
                trade_notify(direction=entry['direction'], entry=entry['price'], size=0.7, tp=entry['tp'], sl=entry['sl'])

        elif open_order:
            result = close_position()
            if result:
                outcome, pnl = result
                capital += pnl
                trade_notify(result=outcome, pnl=pnl, new_cap=capital)

            else:
                updated = check_and_update_sl()
                if updated:
                    trade_notify(f"[MOVE SL] SL moved to entry @ {open_order['entry']}")

        # Health check ทุกๆ 6 ชั่วโมง
        if time.time() - last_health_check > 60 * 60 * 6:
            health_check(capital)
            last_health_check = time.time()

    except Exception as e:
        print("Error:", e)

    time.sleep(CHECK_INTERVAL)
