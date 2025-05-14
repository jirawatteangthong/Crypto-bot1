import time
from config import *
from strategy import get_fibo_zone
from entry import check_entry_signal
from telegram import notify, trade_notify, health_check
from utils import is_new_day

capital = START_CAPITAL
last_health_check = 0

notify("[BOT STARTED] Trading bot is now running.")

while True:
    try:
        fibo, trend, status = get_fibo_zone()

        if status == 'ok':
            entry = check_entry_signal(fibo)
            if entry:
                trade_notify(direction=entry['direction'], entry=entry['entry'], size=ORDER_SIZE, tp=entry['tp'], sl=entry['sl'])
                # simulate close
                result = 'WIN'  # or 'LOSS' based on TP/SL hit
                pnl = 5.0 if result == 'WIN' else -3.0
                capital += pnl
                trade_notify(result=result, pnl=pnl, new_cap=capital)

        if time.time() - last_health_check > HEALTH_CHECK_HOURS * 3600:
            health_check(capital)
            last_health_check = time.time()

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        notify(f"[ERROR] {e}")
        time.sleep(60)
