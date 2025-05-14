import time
from config import *
from strategy import detect_bos_and_swing
from fibonacci import calculate_fibonacci_levels
from order import open_trade, monitor_trades
from telegram import notify, trade_notify, daily_summary
from utils import get_current_timeframe_data, is_new_day

trades_today = 0
positions = []
capital = START_CAPITAL

notify("[BOT STARTED] เริ่มทำงานแล้ว")

while True:
    try:
        if is_new_day():
            daily_summary(capital, trades_today)
            trades_today = 0
            positions = []

        if trades_today >= MAX_TRADES_PER_DAY or positions:
            positions = monitor_trades(positions, capital)
            time.sleep(CHECK_INTERVAL)
            continue

        candles = get_current_timeframe_data(TIMEFRAME)
        trend, swing = detect_bos_and_swing(candles)

        if trend and swing:
            fibo = calculate_fibonacci_levels(swing, trend)
            capital = open_trade(fibo, capital)
            positions.append(fibo)
            trades_today += 1

        positions = monitor_trades(positions, capital)
        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        notify(f"[ERROR] {str(e)}")
        time.sleep(60)
