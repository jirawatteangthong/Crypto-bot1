import time
from config import *
from strategy import get_fibo_zone
from entry import check_entry_signal
from order import open_trade, monitor_trades, get_open_positions
from telegram import notify, health_check
from utils import is_new_day

capital = START_CAPITAL
last_health = time.time()
positions = []
has_traded_today = False

notify("[BOT STARTED] ✅บอทเริ่มทำงานแล้ว💰")
positions = get_open_positions()

while True:
    try:
        if is_new_day():
            positions = []
            has_traded_today = False

        if not has_traded_today:
            fibo, trend, status = get_fibo_zone()
            if status == 'ok':
                signal = check_entry_signal(fibo)
                if signal:
                    capital = open_trade(signal, capital)
                    positions.append(signal)
                    has_traded_today = True

        positions, capital = monitor_trades(positions, capital)

        if time.time() - last_health >= HEALTH_CHECK_HOURS * 3600:
            health_check(capital)
            last_health = time.time()

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        notify(f"[ERROR] {str(e)}")
        time.sleep(60)
