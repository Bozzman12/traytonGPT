# services/backtest.py
import pandas as pd
from models import BacktestRequest

def _ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def run_backtest(df: pd.DataFrame, req: BacktestRequest):
    c = df["Close"]
    ef = _ema(c, req.params.get("fast", 9))
    es = _ema(c, req.params.get("slow", 21))

    # ATR (stop loss calc)
    h, l, pc = df["High"], df["Low"], df["Close"].shift(1)
    tr = (h - l).abs().combine((h - pc).abs(), max).combine((l - pc).abs(), max)
    atr = tr.rolling(14).mean().bfill()

    pos = 0
    entry = sl = tp = None
    trades = []
    equity = 1.0

    for i in range(1, len(c)):
        long_signal = ef.iloc[i-1] <= es.iloc[i-1] and ef.iloc[i] > es.iloc[i]
        exit_signal = ef.iloc[i-1] >= es.iloc[i-1] and ef.iloc[i] < es.iloc[i]

        # Manage open trade
        if pos == 1 and (c.iloc[i] <= sl or c.iloc[i] >= tp or exit_signal):
            pnl = (c.iloc[i] - entry) / entry
            equity *= (1 + pnl)
            trades.append({"entry_idx": int(i_entry), "exit_idx": int(i), "pnl_pct": float(pnl)})
            pos = 0

        # Open trade
        if pos == 0 and long_signal:
            atr_now = atr.iloc[i]
            entry = c.iloc[i]
            sl = entry - req.params.get("atr_mult_sl", 2.0) * atr_now
            tp = entry + req.params.get("tp_rr", 2.0) * (entry - sl)
            pos = 1
            i_entry = i

    pnl_list = [t["pnl_pct"] for t in trades]
    win_rate = sum(1 for x in pnl_list if x > 0) / len(pnl_list) if pnl_list else 0.0

    return {
        "equity_final": equity,
        "num_trades": len(trades),
        "win_rate": win_rate,
        "max_drawdown": float(_max_drawdown_from_trades(trades)),
        "trades": trades
    }

def _max_drawdown_from_trades(trades):
    eq = 1.0
    peak = 1.0
    mdd = 0.0
    for t in trades:
        eq *= (1 + t["pnl_pct"])
        peak = max(peak, eq)
        mdd = min(mdd, (eq - peak) / peak)
    return mdd
