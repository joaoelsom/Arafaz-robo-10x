from flask import Flask
import os
from pybit.unified_trading import HTTP

app = Flask(__name__)

API_KEY = os.getenv("BYBIT_KEY") or os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_SECRET") or os.getenv("BYBIT_API_SECRET")

@app.route('/')
def home():
    if not API_KEY:
        return "<h1>SEM CHAVE NO RENDER</h1><p>Coloca BYBIT_KEY no Environment</p>"
    try:
        client = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)
        bal = client.get_wallet_balance(accountType="UNIFIED")
        saldo = bal['result']['list'][0]['coin'][0]['walletBalance']
        return f"<h1 style='color:green'>CONECTADO! SALDO: ${saldo}</h1><p>Robo 10x Ativo</p>"
    except Exception as e:
        return f"<h1>ERRO BYBIT:</h1><p>{e}</p><p>Se for IP, coloca No IP Restriction na Bybit</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
