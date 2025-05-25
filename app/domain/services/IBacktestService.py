from abc import ABC, abstractmethod

from app.domain.models.backtest.requests.EnqueueBacktestRequestModel import EnqueueBacktestRequestModel
from app.domain.models.backtest.responses.EnqueueBacktestResponseModel import EnqueueBacktestResponseModel


class IBacktestService(ABC):
    @abstractmethod
    async def enqueue_backtest(self, request: EnqueueBacktestRequestModel) -> EnqueueBacktestResponseModel:
        pass