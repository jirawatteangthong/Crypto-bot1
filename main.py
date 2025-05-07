import time
from config import *
from strategy import get_fibo_zone
from entry import get_entry_signals
from order import open_trade, monitor_trades
from telegram import health_check, notify
from utils import is_new_day

capital = START_CAPITAL
last_health = time.time()
has_orders_today = 0
last_day = None

notify("BOT STARTED")

while True:
    now = time.time()

    # รีเซ็ตนับไม้เมื่อขึ้นวันใหม่
    if is_new_day() or last_day != time.strftime('%Y-%m-%d'):
        has_orders_today = 0
        last_day = time.strftime('%Y-%m-%d')
        notify("[NEW DAY] Reset daily order count.")

    # หากยังเปิดไม้ไม่ครบ
    if has_orders_today < 2:
        fibo, trend = get_fibo_zone()
        signals = get_entry_signals(fibo, trend, has_orders_today)

        for signal in signals:
            if has_orders_today >= 2:
                break
            capital = open_trade(signal, capital)
            has_orders_today += 1

    # ติดตามสถานะออเดอร์
    capital = monitor_trades(capital)

    # Health check ทุก 3 ชั่วโมง
    if now - last_health >= 3 * 3600:
        health_check(capital)
        last_health = now

    time.sleep(CHECK_INTERVAL)
