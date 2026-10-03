from flask import Flask
import os
from pybit.unified_trading import HTTP

app = Flask(__name__)

# Pega as chaves que você colocou no Render
API_KEY = os.getenv("BYBIT_KEY")
API_SECRET = os.getenv("BYBIT_SECRET")

@app.route("/")
def home():
    try:
        session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)
        saldo = session.get_wallet_balance(accountType="UNIFIED")
        moedas = saldo['result']['list'][0]['coin']

        total_usd = 0
        html_moedas = ""
        for m in moedas:
            usd = float(m['usdValue'] or 0)
            if usd > 0.01: # só mostra quem tem valor
                total_usd += usd
                html_moedas += f"<p><b>{m['coin']}:</b> {m['walletBalance']} = ${usd:.2f}</p>"

        return f"""
        <body style="background:black;color:white;font-family:Arial;padding:20px">
        <h1 style="color:#00ff00">CONECTADO! ✅</h1>
        <h2>Saldo Total: ${total_usd:.2f}</h2>
        <hr>
        {html_moedas}
        <br><br>
        <p style="color:gray">Robô em Frankfurt - Bybit liberada</p>
        <p style="color:gray">Status: Aguardando sinal de entrada...</p>
        </body>
        """

    except Exception as e:
        return f"<h1 style='color:red'>Erro: {e}</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
