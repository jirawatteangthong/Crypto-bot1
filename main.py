import ccxt
import time
import requests
from statistics import mean, stdev

# === CONFIG ===
API_KEY = '0659b6f2-c86a-466a-82ec-f1a52979bc33'
API_SECRET = 'CCB0A67D53315671F599050FCD712CD1'
API_PASSPHRASE = 'Jirawat1-'

SYMBOL = 'BTC-USDT-SWAP'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

LEVERAGE = 20
BASE_CAPITAL = 20
WITHDRAW_THRESHOLD = 3  # ถอนกำไรทุก 3 ไม้
ORDER_SIZE_PCT = 1.0

capital = BASE_CAPITAL
win_count = 0
position_open = False

# === OKX API ===
okx = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'},
})

# === TELEGRAM NOTIFICATION ===
def telegram(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                     params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except:
        print("[Telegram Error]")

# === SAFELY FETCH OHLCV ===
def get_ohlcv_safe(symbol, tf, limit=50, retries=5):
    for i in range(retries):
        try:
            data = okx.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
            if data and len(data) >= limit:
                return data
        except Exception as e:
            time.sleep(1)
    raise Exception(f"fetch_ohlcv failed: {tf} (after {retries} retries)")

# === MACD CALCULATION ===
def calculate_macd(data, fast=12, slow=26, signal=9):
    def ema(values, period):
        k = 2 / (period + 1)
        ema_val = values[0]
        result = []
        for price in values:
            ema_val = price * k + ema_val * (1 - k)
            result.append(ema_val)
        return result
    macd_line = [f - s for f, s in zip(ema(data, fast), ema(data, slow))]
    signal_line = ema(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, hist

# === GET CURRENT TICKER ===
def get_ticker(symbol):
    try:
        ticker = okx.fetch_ticker(symbol)
        if ticker and 'last' in ticker:
            return ticker['last']  # ราคาปัจจุบัน
        else:
            raise Exception("ไม่พบข้อมูลราคาจาก API")
    except Exception as e:
        telegram(f"[ERROR] fetch_ticker failed: {str(e)}")
        return None

# === CHECK ENTRY CONDITIONS ===
def check_entry():
    try:
        h1 = get_ohlcv_safe(SYMBOL, '1h')
        m15 = get_ohlcv_safe(SYMBOL, '15m')
        m1 = get_ohlcv_safe(SYMBOL, '1m')

        h1_close = [x[4] for x in h1]
        trend_up_h1 = h1_close[-1] > h1_close[-2] > h1_close[-3]  # H1 trend check (Uptrend)

        m15_highs = [x[2] for x in m15[-5:]]
        m15_lows = [x[3] for x in m15[-5:]]
        poi_high = max(m15_highs)
        poi_low = min(m15_lows)

        m1_close = [x[4] for x in m1]
        macd, signal, hist = calculate_macd(m1_close)
        cross_up = macd[-2] < signal[-2] and macd[-1] > signal[-1]  # MACD cross-up
        cross_down = macd[-2] > signal[-2] and macd[-1] < signal[-1]  # MACD cross-down
        price = m1_close[-1]
        price_sd = stdev(m1_close[-20:])
        price_mean = mean(m1_close[-20:])
        inside_deviation = abs(price - price_mean) <= 2 * price_sd

        # ตรวจสอบกรณีเทรนด์ขาขึ้น (Uptrend) และเข้าออเดอร์ Buy
        if trend_up_h1 and price <= poi_low and cross_up and inside_deviation:
            return "long", price
        # ตรวจสอบกรณีเทรนด์ขาลง (Downtrend) และเข้าออเดอร์ Short
        elif not trend_up_h1 and price >= poi_high and cross_down and inside_deviation:
            return "short", price
        
        return None, None
    except Exception as e:
        telegram(f"[ERROR] Strategy check failed: {str(e)}")
        return None, None

# === SET LEVERAGE ===
def set_leverage(symbol, leverage):
    try:
        okx.set_leverage(leverage, symbol, {'marginMode': 'cross'})
    except:
        pass

# === PLACE ORDER ===
def place_order(direction, price, capital):
    # คำนวณขนาดออเดอร์
    size = round((capital * LEVERAGE) / price, 3)
    side = 'buy' if direction == "long" else 'sell'
    sl_side = 'sell' if side == 'buy' else 'buy'
    sl_price = round(price * (0.99 if direction == "long" else 1.01), 2)
    tp_price = round(price * (1 + 0.01 * 2) if direction == "long" else price * (1 - 0.01 * 2), 2)

    # เปิดออเดอร์
    order = okx.create_market_order(SYMBOL, side, size)
    telegram(f"[ENTRY] {direction.upper()} @ {price}\nSize: {size}\nTP: {tp_price}\nSL: {sl_price}")

    # เปิดคำสั่ง OCO
    okx.private_post_trade_order_algo({
        'instId': SYMBOL,
        'tdMode': 'cross',
        'side': sl_side,
        'ordType': 'oco',
        'sz': size,
        'tpTriggerPx': tp_price,
        'tpOrdPx': '-1',
        'slTriggerPx': sl_price,
        'slOrdPx': '-1'
    })

    return size, price, tp_price, sl_price

# === MAIN LOOP ===
def main_loop():
    global position_open, capital, win_count

    telegram("บอทพี่ทำงานแล้ว")
    set_leverage(SYMBOL, LEVERAGE)

    while True:
        if not position_open:
            direction, price = check_entry()
            if direction:
                size, entry, tp, sl = place_order(direction, price, capital)
                position_open = True

                while True:
                    try:
                        ticker = okx.fetch_ticker(SYMBOL)
                        current_price = ticker['last']
                        if (direction == 'long' and current_price >= tp) or (direction == 'short' and current_price <= tp):
                            profit = (tp - entry) * size if direction == "long" else (entry - tp) * size
                            capital += profit
                            win_count += 1
                            telegram(f"[TP HIT] {direction.upper()} +{round(profit, 2)} USDT | Capital: {round(capital,2)}")

                            if win_count % WITHDRAW_THRESHOLD == 0:
                                withdraw_amount = capital / 2
                                capital -= withdraw_amount
                                telegram(f"[WITHDRAW] ถอนกำไรออก {round(withdraw_amount,2)} เหรียญ | เหลือ: {round(capital,2)}")

                            position_open = False
                            break

                        elif (direction == 'long' and current_price <= sl) or (direction == 'short' and current_price >= sl):
                            loss = (entry - sl) * size if direction == "long" else (sl - entry) * size
                            capital -= abs(loss)
                            telegram(f"[SL HIT] {direction.upper()} -{round(abs(loss), 2)} USDT | Capital: {round(capital,2)}")
                            position_open = False
                            break
                    except Exception as e:
                        telegram(f"[ERROR] Price check failed: {e}")
                    time.sleep(5)
        time.sleep(10)

if __name__ == "__main__":
    main_loop()
