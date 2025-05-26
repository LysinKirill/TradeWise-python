from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.exceptions.backtest.BacktestResult import BacktestResult
from dataAccess.models.backtest.BacktestRecord import BacktestRecord
from dataAccess.models.backtest.BacktestStatus import BacktestStatus


class IBacktestRepository(ABC):
    @abstractmethod
    async def create_backtest(
        self,
        user_id: int,
        model_id: int,
        allocated_amount: float,
        from_: datetime,
        to: datetime
    ) -> int:
        pass

    @abstractmethod
    async def get_backtest(self, backtest_id: int) -> BacktestRecord | None:
        pass

    @abstractmethod
    async def get_user_backtests(self, user_id: int) -> list[BacktestRecord]:
        pass

    @abstractmethod
    async def get_first_backtest_by_status(self, status: BacktestStatus) -> BacktestRecord | None:
        pass

    @abstractmethod
    async def update_backtest_status(
        self,
        backtest_id: int,
        status: BacktestStatus,
        started_at: datetime | None = None,
        finished_at:datetime | None = None
    ) -> bool:
        pass

    @abstractmethod
    async def set_backtest_result(self, backtest_result: BacktestResult) -> None:
        pass