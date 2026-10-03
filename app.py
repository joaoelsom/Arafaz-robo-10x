from flask import Flask
import os
import requests

app = Flask(__name__)

API_KEY = os.getenv("BYBIT_KEY") or os.getenv("BYBIT_API_KEY") or os.getenv("BYBIT_API_KEY_")
API_SECRET = os.getenv("BYBIT_SECRET") or os.getenv("BYBIT_API_SECRET")
PROXY_URL = os.getenv("PROXY_URL", "")

@app.route('/')
def home():
    if not API_KEY:
        return "<h1>SEM CHAVE NO RENDER</h1><p>Coloca BYBIT_KEY no Environment do Render</p>"

    try:
        # Usa proxy se tiver
        proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

        from pybit.unified_trading import HTTP

        # Configura proxy no sistema pro pybit usar
        if PROXY_URL:
            os.environ['HTTP_PROXY'] = PROXY_URL
            os.environ['HTTPS_PROXY'] = PROXY_URL

        client = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)
        bal = client.get_wallet_balance(accountType="UNIFIED")

        if 'result' in bal and 'list' in bal['result']:
            saldo = bal['result']['list'][0]['coin']
            total = bal['result']['list'][0].get('totalEquity', '0')
            return f"<h1 style='color:green'>CONECTADO!</h1><h2>Saldo: ${total}</h2><p>{saldo}</p>"
        else:
            return f"<h1 style='color:green'>CONECTADO!</h1><p>{bal}</p>"

    except Exception as e:
        return f"<h1>ERRO BYBIT:</h1><p>{e}</p><p>Se for IP, coloca No IP Restriction na Bybit e adiciona PROXY_URL no Render</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
