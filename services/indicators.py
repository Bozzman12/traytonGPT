import pandas as pd
import yfinance as yf

_VALID_INTERVALS = {"1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"}

def get_ohlc(symbol: str, interval: str = "1d", period: str = "1y") -> pd.DataFrame:
    if interval not in _VALID_INTERVALS:
        interval = "1d"
    df = yf.download(symbol, interval=interval, period=period, progress=False, auto_adjust=False)
    if df.empty and "-USD" not in symbol and "USD" not in symbol:
        df = yf.download(f"{symbol}-USD", interval=interval, period=period, progress=False)
    df = df.dropna()
    if "Volume" not in df.columns:
        df["Volume"] = 0
    return df
