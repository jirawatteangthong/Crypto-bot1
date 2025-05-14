from config import API_KEY, API_SECRET, API_PASSPHRASE

def connect_okx():
    exchange = ccxt.okx({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'password': API_PASSPHRASE,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'
        }
    })
    return exchange
