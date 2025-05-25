from dataclasses import dataclass
from datetime import datetime

from app.domain.models.backtest.BacktestStatusModel import BacktestStatusModel
from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.models.user.UserInfoModel import UserInfoModel


@dataclass(frozen=True)
class BacktestModel:
    id: int
    user_info: UserInfoModel
    model_info: ShortModelInfoModel
    started_at: datetime | None
    finished_at: datetime | None
    test_period_start: datetime | None
    test_period_end: datetime | None
    status: BacktestStatusModel
    profit: float
    trades_count: int
    initial_balance: float
    final_balance: float | None
    created_at: datetime