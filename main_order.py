import time
from config import *
from utils import fetch_current_price, fetch_ohlcv, detect_bos, detect_choch
from telegram import notify_once, trade_notify, health_check, reset_flags
import datetime

capital = START_CAPITAL
open_position = None
fibo_data = None
last_entry_price = None

def in_fibo_zone(price, fibo):
    return fibo['levels']['78.6'] <= price <= fibo['levels']['61.8'] if fibo['direction'] == 'short' else fibo['levels']['61.8'] <= price <= fibo['levels']['78.6']

def calculate_sl_tp(fibo):
    fibo_range = abs(fibo['levels']['0'] - fibo['levels']['100'])
    tp = fibo['levels']['0'] + 0.10 * fibo_range if fibo['direction'] == 'long' else fibo['levels']['0'] - 0.10 * fibo_range
    sl = fibo['levels']['100'] - 0.10 * fibo_range if fibo['direction'] == 'long' else fibo['levels']['100'] + 0.10 * fibo_range
    return tp, sl

def simulate_trade(entry_price, direction, tp, sl):
    global capital
    result = 'WIN' if (direction == 'long' and tp > entry_price) or (direction == 'short' and tp < entry_price) else 'LOSS'
    pnl = ORDER_SIZE * (abs(tp - entry_price)) if result == 'WIN' else -ORDER_SIZE * (abs(sl - entry_price))
    capital += pnl
    return result, pnl

def main_loop():
    global fibo_data, open_position, last_entry_price

    while True:
        try:
            now = datetime.datetime.utcnow()
            if now.hour % HEALTH_CHECK_HOURS == 0 and now.minute == 0:
                health_check(capital)

            h1_candles = fetch_ohlcv('1h')
            m15_candles = fetch_ohlcv('15m')
            m1_candles = fetch_ohlcv('1m')

            trend = detect_bos(h1_candles)
            choch_m15 = detect_choch(m15_candles)

            # Step 1: วาด Fibonacci
            if trend and choch_m15 == trend:
                reset_flags()
                highs = [c[2] for c in h1_candles[-70:]]
                lows = [c[3] for c in h1_candles[-70:]]
                high = max(highs)
                low = min(lows)

                fibo_data = {
                    'direction': 'long' if trend == 'bullish' else 'short',
                    'levels': {
                        '0': high if trend == 'bullish' else low,
                        '100': low if trend == 'bullish' else high,
                        '61.8': low + 0.618 * (high - low) if trend == 'bullish' else high - 0.618 * (high - low),
                        '78.6': low + 0.786 * (high - low) if trend == 'bullish' else high - 0.786 * (high - low)
                    }
                }
                fibo_data['tp'], fibo_data['sl'] = calculate_sl_tp(fibo_data)
                notify_once('draw_fibo', f"[DRAW FIBO] High={high} | Low={low}")
                notify_once('choch_m15', "[CHoCH M15] เกิดสัญญาณเปลี่ยนเทรนด์จาก M15")

            # Step 2: ตรวจเข้าโซน Fibo
            if fibo_data:
                price = fetch_current_price()
                if in_fibo_zone(price, fibo_data) and open_position is None:
                    notify_once('enter_zone', f"[ENTER ZONE] Price: {price:.2f} เข้าระหว่าง {fibo_data['levels']['61.8']:.2f} - {fibo_data['levels']['78.6']:.2f}")

                    # Step 3: มองหา CHoCH ใน M1 ยืนยันการกลับตัว
                    m1_choch = detect_choch(m1_candles)
                    if m1_choch == fibo_data['direction']:
                        open_position = {
                            'direction': fibo_data['direction'],
                            'entry': price,
                            'tp': fibo_data['tp'],
                            'sl': fibo_data['sl']
                        }
                        last_entry_price = price
                        trade_notify(direction=fibo_data['direction'], entry=price, size=0.7, tp=fibo_data['tp'], sl=fibo_data['sl'])

            # Step 4: ตรวจปิดออเดอร์
            if open_position:
                price = fetch_current_price()
                if (open_position['direction'] == 'long' and price >= open_position['tp']) or (open_position['direction'] == 'short' and price <= open_position['tp']):
                    result, pnl = simulate_trade(open_position['entry'], open_position['direction'], open_position['tp'], open_position['sl'])
                    trade_notify(result=result, pnl=pnl, new_cap=capital)
                    open_position = None
                elif (open_position['direction'] == 'long' and price <= open_position['sl']) or (open_position['direction'] == 'short' and price >= open_position['sl']):
                    result, pnl = simulate_trade(open_position['entry'], open_position['direction'], open_position['tp'], open_position['sl'])
                    trade_notify(result=result, pnl=pnl, new_cap=capital)
                    open_position = None

        except Exception as e:
            notify_once('error', f"[ERROR] {str(e)}")

        time.sleep(CHECK_INTERVAL)

# เริ่มทำงาน
notify_once('bot_started', "[BOT STARTED] ระบบเริ่มทำงานแล้ว")
main_loop()
