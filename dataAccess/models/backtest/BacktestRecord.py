from dataclasses import dataclass
from datetime import datetime
from dataAccess.models.backtest.BacktestStatus import BacktestStatus
from dataAccess.models.common.UserInfo import UserInfo
from dataAccess.models.model.ShortModelInfo import ShortModelInfo


@dataclass(frozen=True)
class BacktestRecord:
    id: int
    user_info: UserInfo
    model_info: ShortModelInfo
    started_at: datetime | None
    finished_at: datetime | None
    test_period_start: datetime | None
    test_period_end: datetime | None
    status: BacktestStatus
    profit: float
    trades_count: int
    initial_balance: float
    final_balance: float | None
    created_at: datetime

    @classmethod
    def from_query_row(
            cls,
            id: int,
            user_id: int,
            email: str,
            invest_api_key: str,
            invest_account_id: str,
            model_id: int,
            instrument_id: str,
            model_name: str,
            model_type: str,
            model_created_at: datetime,
            started_at: datetime | None,
            finished_at: datetime | None,
            test_period_start: datetime,
            test_period_end: datetime,
            status: str,
            profit: float,
            trades_count: int,
            initial_balance: float,
            final_balance: float | None,
            created_at: datetime,
    ):
        return cls(
            id=id,
            user_info=UserInfo(
                id=user_id,
                email=email,
                invest_api_key=invest_api_key,
                invest_account_id=invest_account_id,
            ),
            model_info=ShortModelInfo(
                id=model_id,
                instrument_id=instrument_id,
                name=model_name,
                model_type=model_type,
                created_at=model_created_at,
            ),
            started_at=started_at,
            finished_at=finished_at,
            test_period_start=test_period_start,
            test_period_end=test_period_end,
            status=BacktestStatus(status),
            profit=profit,
            trades_count=trades_count,
            initial_balance=initial_balance,
            final_balance=final_balance,
            created_at=created_at
        )
