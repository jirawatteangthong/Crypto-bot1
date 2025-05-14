import time
from strategy import analyze_market
from order import check_open_orders, open_trade, update_trade_status
from telegram import send_message
from utils import is_new_day, summarize_daily_trades

send_message("บอทเริ่มทำงาน")

daily_trade_count = 0
current_date = time.strftime("%Y-%m-%d")

while True:
    try:
        if is_new_day(current_date):
            current_date = time.strftime("%Y-%m-%d")
            daily_trade_count = 0
            summarize_daily_trades()

        if check_open_orders():
            update_trade_status()
        elif daily_trade_count < 5:
            signal = analyze_market()
            if signal:
                open_trade(signal)
                daily_trade_count += 1

        time.sleep(15)

    except Exception as e:
        send_message(f"ERROR: {e}")
        time.sleep(60)
