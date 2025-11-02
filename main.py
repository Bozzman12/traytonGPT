from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from services.market import get_ohlc
from services.indicators import compute_indicators, infer_trend
from services.patterns import detect_patterns
from models import BacktestRequest
from services.backtest import run_backtest
from services.patterns import detect_patterns


app = FastAPI(title="Trayton Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ohlc")
def ohlc(symbol: str, interval: str = "1d", period: str = "1y"):
    df = get_ohlc(symbol=symbol, interval=interval, period=period)
    return df.reset_index().to_dict(orient="records")

@app.get("/indicators")
def indicators(symbol: str, interval: str = "1d", period: str = "1y", ind: Optional[str] = "sma20,sma50,rsi,macd,bbands"):
    df = get_ohlc(symbol=symbol, interval=interval, period=period)
    wanted = [s.strip().lower() for s in ind.split(",")] if ind else []
    return compute_indicators(df, wanted)

@app.get("/trend")
def trend(symbol: str, interval: str = "1d", period: str = "6mo"):
    df = get_ohlc(symbol=symbol, interval=interval, period=period)
    return infer_trend(df)

@app.get("/patterns")
def patterns(symbol: str, interval: str = "1d", period: str = "1y", types: Optional[str] = "head_shoulders,flag"):
    df = get_ohlc(symbol=symbol, interval=interval, period=period)
    wanted = [t.strip().lower() for t in types.split(",")] if types else []
    return detect_patterns(df, wanted)

@app.post("/backtest/run")
def backtest(req: BacktestRequest):
    df = get_ohlc(symbol=req.symbol, interval=req.tf, period=req.period or "2y")
    return run_backtest(df, req)
