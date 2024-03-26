from datetime import datetime

import pandas as pd
import settrade_v2
import yfinance as yf
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from settrade_v2.errors import SettradeError

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")
investor = settrade_v2.Investor(
    app_id="vUc1eWD7czqD3jxe",
    app_secret="AI9WU6VBoVz6KABgCUikAFCh175K0H5Pmt0lN0RRLSN7",
    broker_id="SANDBOX",
    app_code="SANDBOX",
    is_auto_queue=False,
)
deri = investor.Derivatives(account_no="64160038-D")
market = investor.MarketData()


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/portfolios")
def portfolios(request: Request):
    return deri.get_portfolios()


@app.get("/orders")
def orders(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={"request": request, "orders": deri.get_orders()},
    )


@app.get("/dashboard/{symbol}")
def dashboard(request: Request, symbol: str):

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "symbol": symbol,
        },
    )


@app.get("/api/sp_500_history")
def set50_history():
    sp_500 = yf.Ticker("^GSPC")
    sp_500 = sp_500.history(period="1Y")
    sp_500.reset_index(inplace=True)
    sp_500 = sp_500[["Date", "Open"]]
    sp_500["Date"] = sp_500["Date"].dt.strftime("%Y-%m-%d")
    return sp_500.to_dict(orient="records")


@app.get("/api/sp_500_prediction")
def set50_prediction():
    df = pd.read_csv("assets/predictions.csv")
    sp_500_pred = df.query("item_id == 'S&P500'")
    return sp_500_pred.to_dict(orient="records")


@app.get("/api/set50_history")
def set50_history():
    set50 = yf.Ticker("^SET.BK")
    set50 = set50.history(period="1Y")
    set50.reset_index(inplace=True)
    set50 = set50[["Date", "Open"]]
    set50["Date"] = set50["Date"].dt.strftime("%Y-%m-%d")
    return set50.to_dict(orient="records")


@app.get("/api/set50_prediction")
def set50_prediction():
    df = pd.read_csv("assets/predictions.csv")
    set50_pred = df.query("item_id == 'SET50'")
    return set50_pred.to_dict(orient="records")


@app.get("/api/csi300_history")
def csi300_history():
    csi300 = yf.Ticker("000300.SS")
    csi300 = csi300.history(period="1Y")
    csi300.reset_index(inplace=True)
    csi300 = csi300[["Date", "Open"]]
    csi300["Date"] = csi300["Date"].dt.strftime("%Y-%m-%d")
    return csi300.to_dict(orient="records")


@app.get("/api/csi300_prediction")
def csi300_prediction():
    df = pd.read_csv("assets/predictions.csv")
    csi300_pred = df.query("item_id == 'CSI300'")
    return csi300_pred.to_dict(orient="records")


@app.get("/api/ni225_history")
def ni225_history():
    ni225 = yf.Ticker("^N225")
    ni225 = ni225.history(period="1Y")
    ni225.reset_index(inplace=True)
    ni225 = ni225[["Date", "Open"]]
    ni225["Date"] = ni225["Date"].dt.strftime("%Y-%m-%d")
    return ni225.to_dict(orient="records")


@app.get("/api/ni225_prediction")
def ni225_prediction():
    df = pd.read_csv("assets/predictions.csv")
    ni225_pred = df.query("item_id == 'NI225'")
    return ni225_pred.to_dict(orient="records")


def get_quote(symbol: str) -> float:
    try:
        quote = market.get_quote_symbol(symbol)
        print(quote)

        price = float(quote["low"])
        return price
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/candlestick/{symbol}/{interval}/{start}/{end}")
def get_candlestick(symbol: str, interval: str, start: str, end: str):
    try:
        data = market.get_candlestick(
            symbol=symbol, interval=interval, limit=None, start=start, end=end
        )
        print(data)
    except SettradeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return data


@app.get("/api/orders")
def get_all_orders():
    try:
        print(deri.get_orders())
        orders = sorted(deri.get_orders(), key=lambda d: d["orderNo"], reverse=True)
    except SettradeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return orders


@app.get("/api/current_quote/{symbol}")
def current_quote(symbol: str) -> dict:
    # try to get current price of symbol
    try:
        price = get_quote(symbol)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail=str(e))
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return {"symbol": symbol, "price": price, "datetime": dt_string}


@app.get("/api/buy/{symbol}/{qty}")
def buy(symbol: str, qty: int):
    try:
        order = deri.place_order(
            pin="000000",
            symbol=symbol,
            side="Long",
            position="Open",
            price_type="Limit",
            price=get_quote(symbol),
            volume=qty,
        )
        print(order)
    except SettradeError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    return order


@app.get("/api/sell/{symbol}/{qty}")
def sell(symbol: str, qty: int):
    try:
        order = deri.place_order(
            pin="000000",
            symbol=symbol,
            side="Short",
            position="Open",
            price_type="Limit",
            price=get_quote(symbol),
            volume=qty,
        )
    except SettradeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order


@app.get("/api/cancelOrder/{order_no}")
def cancel_order(order_no: str):
    try:
        order = deri.cancel_order(order_no=order_no, pin="000000")
    except SettradeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order
