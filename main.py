import ccxt
import time
import requests
from statistics import mean, stdev

# === CONFIG ===
API_KEY          = '0659b6f2-c86a-466a-82ec-f1a52979bc33'
API_SECRET       = 'CCB0A67D53315671F599050FCD712CD1'
API_PASSPHRASE   = 'Jirawat1-'
SYMBOL           = 'BTC-USDT-SWAP'
TELEGRAM_TOKEN   = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

LEVERAGE           = 20
BASE_CAPITAL       = 20
WITHDRAW_THRESHOLD = 3    # ถอนทุก 3 ไม้
BE_TRIGGER_RATIO   = 0.5  # 50% ของทางไป TP

capital       = BASE_CAPITAL
win_count     = 0
position_open = False

# === OKX API CLIENT ===
okx = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'},
})

# === TELEGRAM FUNCTION WITH DEBUG ===
def telegram(msg):
    try:
        print("Sending Telegram:", msg)
        resp = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            params={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
        print("Telegram response:", resp.status_code, resp.text)
    except Exception as e:
        print("[Telegram Error]", e)

# === SAFE OHLCV FETCH ===
def get_ohlcv_safe(symbol, tf, limit=50, retries=5):
    for _ in range(retries):
        try:
            data = okx.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
            if data and len(data) >= limit:
                return data
        except Exception as e:
            print(f"[ERROR] fetch_ohlcv {tf}: {e}")
            time.sleep(1)
    raise Exception(f"fetch_ohlcv failed: {tf}")

# === MACD CALCULATION ===
def calculate_macd(data, fast=12, slow=26, signal=9):
    def ema(vals, period):
        k = 2/(period+1)
        e = vals[0]
        out = []
        for v in vals:
            e = v*k + e*(1-k)
            out.append(e)
        return out

    macd_line = [a-b for a,b in zip(ema(data, fast), ema(data, slow))]
    sig_line  = ema(macd_line, signal)
    hist      = [m-s for m,s in zip(macd_line, sig_line)]
    return macd_line, sig_line, hist

# === ENTRY SIGNAL LOGIC ===
def check_entry():
    try:
        h1  = get_ohlcv_safe(SYMBOL, '1h')
        m15 = get_ohlcv_safe(SYMBOL, '15m')
        m1  = get_ohlcv_safe(SYMBOL, '1m')

        closes_h1 = [x[4] for x in h1]
        uptrend   = closes_h1[-1] > closes_h1[-2] > closes_h1[-3]

        highs15 = [x[2] for x in m15[-5:]]
        lows15  = [x[3] for x in m15[-5:]]
        poi_h   = max(highs15)
        poi_l   = min(lows15)

        closes1 = [x[4] for x in m1]
        macd, sig, _ = calculate_macd(closes1)
        cross_up   = macd[-2]<sig[-2] and macd[-1]>sig[-1]
        cross_down = macd[-2]>sig[-2] and macd[-1]<sig[-1]

        price      = closes1[-1]
        sd, mu     = stdev(closes1[-20:]), mean(closes1[-20:])
        inside_dev = abs(price-mu) <= 2*sd

       # ส่ง debug สถานะตัวแปรสำคัญไป Telegram
       telegram(f"[DEBUG] uptrend={uptrend}, price={price:.2f}, poi_low={poi_low:.2f}, cross_up={cross_up}, inside_dev={inside_dev}")

        if uptrend and price<=poi_l and cross_up and inside_dev:
            return "long", price
        if not uptrend and price>=poi_h and cross_down and inside_dev:
            return "short", price
        return None, None
    except Exception as e:
        telegram(f"[ERROR] Strategy failed: {e}")
        return None, None

# === SET LEVERAGE ===
def set_leverage():
    try:
        okx.set_leverage(LEVERAGE, SYMBOL, {'marginMode':'cross'})
    except Exception as e:
        print("[ERROR] set_leverage:", e)

# === PLACE ORDER & OCO SL/TP ===
def place_order(direction, price):
    global capital
    size = round((capital*LEVERAGE)/price,3)
    side = 'buy' if direction=='long' else 'sell'
    sl_side = 'sell' if side=='buy' else 'buy'

    sl_price = round(price*(0.99 if direction=='long' else 1.01),2)
    tp_price = round(price*(1 + 0.01*2) if direction=='long' else price*(1-0.01*2),2)

    okx.create_market_order(SYMBOL, side, size)
    telegram(f"[ENTRY] {direction.upper()} @ {price:.2f}  TP:{tp_price:.2f} SL:{sl_price:.2f}")

    okx.private_post_trade_order_algo({
        'instId': SYMBOL, 'tdMode':'cross',
        'side': sl_side, 'ordType':'oco',
        'sz': size,
        'tpTriggerPx': tp_price, 'tpOrdPx':'-1',
        'slTriggerPx': sl_price,   'slOrdPx':'-1'
    })

    return size, price, tp_price, sl_price

# === MAIN LOOP ===
def main_loop():
    global position_open, capital, win_count

    telegram("🚀 BOT STARTED")
    set_leverage()

    while True:
    if not position_open:
        # -- DEBUG print ก่อนเช็คสัญญาณ --
        print("⏱️ Checking for entry…")  
        
        direction, entry = check_entry()
        
        # ดูผลลัพธ์ที่ฟังก์ชันคืนมา
        print(f"   → check_entry returned: {direction}, {entry}")
        if direction:
            telegram(f"[DEBUG] Got entry signal: {direction} @ {entry}")
        
        …
            if direction:
                size, entry, tp, sl = place_order(direction, entry)
                position_open = True

                while True:
                    try:
                        ticker = okx.fetch_ticker(SYMBOL)
                        price = ticker.get('last')
                        if price is None:
                            raise Exception("no 'last' in ticker")

                        # Move SL → BE
                        be_price = entry*(1+0.0001) if direction=='long' else entry*(1-0.0001)
                        if direction=='long' and price>= entry + (tp-entry)*BE_TRIGGER_RATIO:
                            okx.private_post_trade_order_algo({
                                'instId':SYMBOL,'tdMode':'cross',
                                'side':'sell','ordType':'reduce_only',
                                'sz':size,'slTriggerPx':round(be_price,2),'slOrdPx':'-1'
                            })
                            telegram(f"[BE] SL→BE @ {be_price:.2f}")
                            sl = be_price
                        if direction=='short' and price<= entry - (entry-tp)*BE_TRIGGER_RATIO:
                            okx.private_post_trade_order_algo({
                                'instId':SYMBOL,'tdMode':'cross',
                                'side':'buy','ordType':'reduce_only',
                                'sz':size,'slTriggerPx':round(be_price,2),'slOrdPx':'-1'
                            })
                            telegram(f"[BE] SL→BE @ {be_price:.2f}")
                            sl = be_price

                        # TP hit
                        if (direction=='long' and price>=tp) or (direction=='short' and price<=tp):
                            pnl = (tp-entry)*size if direction=='long' else (entry-tp)*size
                            capital += pnl; win_count += 1
                            telegram(f"[TP] +{pnl:.2f} | Capital:{capital:.2f}")
                            if win_count % WITHDRAW_THRESHOLD==0:
                                wd=capital/2; capital-=wd
                                telegram(f"[WD] Withdraw {wd:.2f} | Remain:{capital:.2f}")
                            position_open=False
                            break

                        # SL hit
                        if (direction=='long' and price<=sl) or (direction=='short' and price>=sl):
                            pnl = (entry-sl)*size if direction=='long' else (sl-entry)*size
                            capital -= abs(pnl)
                            telegram(f"[SL] -{abs(pnl):.2f} | Capital:{capital:.2f}")
                            position_open=False
                            break

                    except Exception as e:
                        telegram(f"[ERROR] Price loop: {e}")
                    time.sleep(5)
        time.sleep(10)

if __name__ == "__main__":
    # test telegram function immediately
    telegram("🔧 Test Telegram — BOT is up")
    main_loop()
