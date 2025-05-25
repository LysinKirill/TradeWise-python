from dataclasses import dataclass


@dataclass(frozen=True)
class EnqueueBacktestResponseModel:
    backtest_id: int
