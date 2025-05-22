from abc import ABC, abstractmethod

from ml.data.model.OperationType import OperationType
from ml.data.model.responses.GetPortfolioResponse import GetPortfolioResponse


class IBroker(ABC):
    @abstractmethod
    async def load_instrument(self, instrument_id: str, invest_api_key: str):
        pass

    @abstractmethod
    async def get_portfolio(
            self,
            invest_api_key: str,
            account_id: str,
            instrument_id: str, ) -> GetPortfolioResponse:
        pass

    @abstractmethod
    async def get_portfolio_value(self, current_price: float | None = None) -> float | None:
        pass

    async def place_order(
            self,
            invest_api_key: str,
            account_id: str,
            instrument_id: str,
            operation: OperationType,
            quantity: int,
            expected_price: float | None = None
    ):
        pass

    @abstractmethod
    async def get_max_lots(
            self,
            invest_api_key: str,
            instrument_id: str,
            account_id: str,
            operation: OperationType,
            expected_price: float | None = None
    ) -> int:
        pass
