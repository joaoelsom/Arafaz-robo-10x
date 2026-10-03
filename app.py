from flask import Flask, render_template_string
import os, threading, time
from pybit.unified_trading import HTTP

app = Flask(__name__)

API_KEY = os.getenv("BYBIT_KEY")
API_SECRET = os.getenv("BYBIT_SECRET")
session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

# CONFIGURAÇÃO SUA
SYMBOL = "BTCUSDT"
LEVERAGE = "10"
STOP_LOSS_BRL = 1.00
TAKE_PROFIT_BRL = 1.60
# Converte pra USD (aprox R$5,40 = $1)
STOP_USD = STOP_LOSS_BRL / 5.4
TAKE_USD = TAKE_PROFIT_BRL / 5.4

status_global = "Robô iniciado - Aguardando..."

def set_leverage():
    try:
        session.set_leverage(category="linear", symbol=SYMBOL, buyLeverage=LEVERAGE, sellLeverage=LEVERAGE)
    except: pass

def trading_loop():
    global status_global
    set_leverage()
    lado = "Buy" # começa comprado
    while True:
        try:
            # Pega preço atual
            preco = float(session.get_tickers(category="linear", symbol=SYMBOL)['result']['list'][0]['lastPrice'])

            # Verifica se tem posição
            pos = session.get_positions(category="linear", symbol=SYMBOL)['result']['list'][0]
            size = float(pos['size'])

            if size == 0: # SEM POSIÇÃO - ENTRA
                # Calcula quantidade pra perder só R$1 (stop de ~0,15% no BTC com 10x)
                # Para 10x, com $19, vamos entrar com ~$5 de margem = $50 de posição
                qty = 0.001 # 0.001 BTC ~ $60 com 10x = margem de $6
                session.place_order(category="linear", symbol=SYMBOL, side=lado, orderType="Market", qty=str(qty))
                status_global = f"Entrou {lado} em {preco} - Stop -R$1 / Alvo +R$1,60"
                time.sleep(5)
            else:
                # COM POSIÇÃO - VERIFICA LUCRO/PREJU
                pnl = float(pos['unrealisedPnl'])
                status_global = f"Em operação {pos['side']} | PnL: ${pnl:.2f} (Alvo +${TAKE_USD:.2f} / Stop -${STOP_USD:.2f}) | Preço: {preco}"

                if pnl >= TAKE_USD or pnl <= -STOP_USD:
                    # FECHA
                    close_side = "Sell" if pos['side'] == "Buy" else "Buy"
                    session.place_order(category="linear", symbol=SYMBOL, side=close_side, orderType="Market", qty=str(size), reduceOnly=True)
                    resultado = "GANHOU" if pnl > 0 else "PERDEU"
                    status_global = f"{resultado} ${pnl:.2f}! Fechou. Invertendo..."
                    # Inverte o lado
                    lado = "Sell" if lado == "Buy" else "Buy"
                    time.sleep(10)

        except Exception as e:
            status_global = f"Erro no loop: {e}"

        time.sleep(3)

# Inicia o robô em segundo plano
threading.Thread(target=trading_loop, daemon=True).start()

@app.route("/")
def home():
    try:
        saldo = session.get_wallet_balance(accountType="UNIFIED")['result']['list'][0]['coin']
        total = sum([float(c['usdValue'] or 0) for c in saldo if float(c['usdValue'] or 0) > 0.01])
        html_moedas = "".join([f"<p>{c['coin']}: {c['walletBalance']}</p>" for c in saldo if float(c['usdValue'] or 0) > 0.01])

        return f"""
        <body style="background:black;color:white;font-family:Arial;padding:20px">
        <h2 style="color:#00ff00">ROBÔ 10X ATIVO ✅</h2>
        <h3>Saldo: ${total:.2f}</h3>
        <div style="background:#111;padding:15px;border-radius:10px;border:1px solid #00ff00">
        <p><b>Par:</b> BTCUSDT 10x</p>
        <p><b>Estratégia:</b> Long/Short alternado</p>
        <p><b>Stop:</b> -R$1,00 / Alvo +R$1,60</p>
        <hr>
        <p style="color:yellow"><b>STATUS:</b><br>{status_global}</p>
        </div>
        <br>{html_moedas}
        <br><p style="color:gray;font-size:12px">Atualiza a página pra ver o status</p>
        </body>
        """
    except Exception as e:
        return f"Erro: {e} <br> Status: {status_global}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
