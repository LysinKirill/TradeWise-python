from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BacktestResult:
    backtest_id: int
    profit: float
    trades_count: int
    final_balance: float
    start_timestamp: datetime
    end_timestamp: datetime