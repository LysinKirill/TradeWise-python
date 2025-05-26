from dataclasses import dataclass
from app.domain.models.backtest.BacktestModel import BacktestModel


@dataclass(frozen=True)
class GetBacktestForUserResponseModel:
    backtests: list[BacktestModel]