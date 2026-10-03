import os, time, hmac, hashlib, threading, requests
from flask import Flask
from datetime import datetime
app = Flask(__name__)
API_KEY = os.getenv("BYBIT_KEY", "")
API_SECRET = os.getenv("BYBIT_SECRET", "")
SYMBOL = "BTCUSDT"
QTY = "0.001"
STOP_LOSS_USDT = -0.18
TAKE_PROFIT_USDT = 0.30
logs = []
saldo = "Aguardando..."
pnl_atual = 0
historico = {"ganho": 0, "perda": 0, "total": 0, "qtd": 0}
status = "Iniciando..."
def bybit_req(method, endpoint, params="", body=None):
    if not API_KEY: return {}
    t = str(int(time.time()*1000))
    payload = t + API_KEY + "5000" + params
    sign = hmac.new(API_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    headers = {"X-BAPI-API-KEY": API_KEY, "X-BAPI-TIMESTAMP": t, "X-BAPI-SIGN": sign, "X-BAPI-RECV-WINDOW": "5000", "Content-Type": "application/json"}
    url = f"https://api.bybit.com{endpoint}" + (f"?{params}" if params else "")
    try:
        r = requests.request(method, url, headers=headers, json=body, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
def log_msg(msg):
    global logs
    logs.append(f"{datetime.now().strftime('%H:%M:%S')} {msg}")
    if len(logs) > 100: logs = logs[-100:]
def bot_loop():
    global saldo, pnl_atual, historico, status
    while True:
        try:
            if not API_KEY:
                status = "Coloque BYBIT_KEY e BYBIT_SECRET no Render"
                time.sleep(10)
                continue
            pos_data = bybit_req("GET", "/v5/position/list", f"category=linear&symbol={SYMBOL}")
            bal_data = bybit_req("GET", "/v5/account/wallet-balance", "accountType=UNIFIED")
            p = (pos_data.get("result", {}).get("list") or [{}])[0]
            size = float(p.get("size", 0))
            unreal = float(p.get("unrealisedPnl", 0))
            pnl_atual = unreal
            equity = 0
            try: equity = float(bal_data["result"]["list"][0]["totalEquity"])
            except: pass
            saldo = f"USDT {equity:.2f}"
            if size == 0:
                bybit_req("POST", "/v5/position/set-leverage", "", {"category":"linear","symbol":SYMBOL,"buyLeverage":"10","sellLeverage":"10"})
                bybit_req("POST", "/v5/order/create", "", {"category":"linear","symbol":SYMBOL,"side":"Buy","orderType":"Market","qty":QTY})
                log_msg(f"-> ABRIU 10x {SYMBOL}")
                status = f"Comprou 10x {datetime.now().strftime('%H:%M:%S')}"
            else:
                status = f"Operando 10x PnL {unreal:.4f}"
                if unreal <= STOP_LOSS_USDT or unreal >= TAKE_PROFIT_USDT:
                    side = "Sell" if p.get("side") == "Buy" else "Buy"
                    bybit_req("POST", "/v5/order/create", "", {"category":"linear","symbol":SYMBOL,"side":side,"orderType":"Market","qty":str(p["size"])})
                    brl = unreal * 5.6
                    historico["total"] += brl
                    historico["qtd"] += 1
                    if brl > 0: historico["ganho"] += brl
                    else: historico["perda"] += brl
                    log_msg(f"<- FECHOU R$ {brl:.2f}")
            time.sleep(10)
        except Exception as e:
            log_msg(f"ERRO {e}")
            time.sleep(10)
threading.Thread(target=bot_loop, daemon=True).start()
@app.route("/")
def painel():
    return f"""<html><head><meta http-equiv="refresh" content="5"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="background:#080808;color:#fff;font-family:sans-serif;padding:15px">
    <div style="max-width:500px;margin:auto;background:#111;border:1px solid #222;border-radius:20px;padding:20px">
    <h2>🤖 ARAFZ 10X <span style="color:#00ff66">● AO VIVO</span></h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <div style="background:#1a1a1a;padding:12px;border-radius:12px">SALDO<br><b>{saldo}</b></div>
      <div style="background:#1a1a1a;padding:12px;border-radius:12px">STOP<br><b>-R$1 / +R$1,70 10x</b></div>
    </div>
    <div style="background:#000;margin-top:12px;padding:12px;border-radius:12px">STATUS: <b>{status}</b><br>PnL: {pnl_atual:.4f}</div>
    <div style="background:#000;margin-top:10px;padding:10px;border-radius:12px;height:220px;overflow:auto;font-family:monospace;font-size:12px;color:#00ff66">{'<br>'.join(reversed(logs[-20:]))}</div>
    </div></body></html>"""
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
