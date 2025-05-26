from abc import ABC, abstractmethod
from app.domain.models.backtest.BacktestModel import BacktestModel
from app.domain.models.backtest.BacktestStatusModel import BacktestStatusModel
from app.domain.models.backtest.requests.EnqueueBacktestRequestModel import EnqueueBacktestRequestModel
from app.domain.models.backtest.responses.EnqueueBacktestResponseModel import EnqueueBacktestResponseModel


class IBacktestService(ABC):
    @abstractmethod
    async def enqueue_backtest(self, request: EnqueueBacktestRequestModel) -> EnqueueBacktestResponseModel:
        pass

    @abstractmethod
    async def get_backtest(self, backtest_id: int) -> BacktestModel:
        pass

    @abstractmethod
    async def get_backtest_status(self, backtest_id: int) -> BacktestStatusModel:
        pass

    @abstractmethod
    async def get_first_backtest_by_status(self, status: BacktestStatusModel) -> BacktestModel | None:
        pass

    @abstractmethod
    async def run_backtest(self, backtest_id: int) -> None:
        pass

    @abstractmethod
    async def cancel_backtest(self, backtest_id: int) -> None:
        pass

    @abstractmethod
    async def update_backtest_status(self, backtest_id: int, status: BacktestStatusModel) -> None:
        pass
