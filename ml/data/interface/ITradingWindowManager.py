from abc import ABC, abstractmethod
from datetime import datetime


class ITradingWindowManager(ABC):
    @abstractmethod
    async def check_trade_available(
        self,
        instrument_id: str,
        timestamp: datetime,
    ):
        pass