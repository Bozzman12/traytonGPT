from pydantic import BaseModel
from typing import Optional, Dict, Any

class BacktestRequest(BaseModel):
    symbol: str
    tf: str = "1d"
    period: Optional[str] = "2y"
    strategy: str = "ema_cross"
    params: Dict[str, Any] = {
        "fast": 9,
        "slow": 21,
        "risk_per_trade": 0.01,
        "atr_mult_sl": 2.0,
        "tp_rr": 2.0
    }
