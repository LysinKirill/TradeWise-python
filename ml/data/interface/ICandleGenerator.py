from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from app.domain.models.invest.CandleModel import CandleModel


class ICandleGenerator(ABC):
    @abstractmethod
    async def generate_candles(self, instrument_id: str, preload_candles_count: int = 0) -> AsyncGenerator[CandleModel | None, None]:
        pass
