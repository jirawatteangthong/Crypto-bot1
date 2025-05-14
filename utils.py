import ccxt
from config import API_KEY, API_SECRET, API_PASSPHRASE

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange.set_leverage(20, 'BTC-USDT-SWAP')
