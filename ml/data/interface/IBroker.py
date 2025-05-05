from abc import ABC, abstractmethod

from ml.data.model.OperationType import OperationType
from ml.data.model.responses.GetPortfolioResponse import GetPortfolioResponse


class IBroker(ABC):
    @abstractmethod
    async def load_instrument(self):
        pass

    @abstractmethod
    async def get_portfolio(self) -> GetPortfolioResponse:
        pass

    @abstractmethod
    async def place_order(
            self,
            operation: OperationType,
            quantity: int,
            expected_price: float | None = None
    ):
        pass

    @abstractmethod
    async def get_max_lots(self, operation: OperationType, expected_price: float | None = None) -> int:
        pass
