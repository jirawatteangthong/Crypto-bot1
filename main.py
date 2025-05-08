import time
from config import *
from strategy import get_fibo_zone
from entry import check_entry_signals
from order import open_trade, monitor_trades
from telegram import notify, health_check
from utils import is_new_day

capital = START_CAPITAL
last_health = time.time()
orders_today = 0
positions = []
notified_no_trade = False
notified_skip_trade = False

notify("[BOT STARTED] ระบบเริ่มทำงานแล้ว")

while True:
    try:
        if is_new_day():
            orders_today = 0
            positions = []
            notified_no_trade = False
            notified_skip_trade = False

        if orders_today < 2:
            fibo, trend_h1, status = get_fibo_zone()

            if status == 'skip' and not notified_skip_trade:
                notify("[SKIP TRADE] เทรนด์สวนทาง → ข้าม")
                notified_skip_trade = True

            if fibo:
                signals = check_entry_signals(fibo, trend_h1)
                for sig in signals:
                    if orders_today >= 2:
                        break
                    if sig['level'] not in [p['level'] for p in positions]:
                        capital = open_trade(sig, capital)
                        positions.append(sig)
                        orders_today += 1

        positions, capital = monitor_trades(positions, capital)

        if time.time() - last_health >= HEALTH_CHECK_HOURS * 3600:
            health_check(capital)
            last_health = time.time()

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        notify(f"[ERROR] {str(e)}")
        time.sleep(60)
