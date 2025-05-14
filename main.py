from config import SYMBOL, TIMEFRAME, MAX_TRADES_PER_DAY
from telegram import send_message
from okx_api import connect_okx
from strategy import detect_bos, get_fibonacci
from order import open_trade
from utils import sleep_until_next_candle, get_today

def fetch_ohlcv(exchange):
    bars = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=50)
    return [{'timestamp': b[0], 'open': b[1], 'high': b[2], 'low': b[3], 'close': b[4]} for b in bars]

def main():
    send_message("✅ บอทเทรด BTC Futures เริ่มทำงานแล้ว")
    exchange = connect_okx()
    trades_today = 0
    trade_date = get_today()

    while True:
        sleep_until_next_candle(TIMEFRAME)

        if get_today() != trade_date:
            trades_today = 0
            trade_date = get_today()

        if trades_today >= MAX_TRADES_PER_DAY:
            continue

        candles = fetch_ohlcv(exchange)
        trend = detect_bos(candles)
        if not trend:
            continue

        high = max(c['high'] for c in candles[-10:])
        low = min(c['low'] for c in candles[-10:])

        if trend == 'up':
            fib_entry, fib_sl = get_fibonacci(high, low)
            tp = fib_entry + (fib_sl - fib_entry)
            open_trade(exchange, 'long', fib_entry, fib_sl, tp)
        elif trend == 'down':
            fib_entry, fib_sl = get_fibonacci(low, high)
            tp = fib_entry - (fib_entry - fib_sl)
            open_trade(exchange, 'short', fib_entry, fib_sl, tp)

        trades_today += 1

if __name__ == "__main__":
    main()
