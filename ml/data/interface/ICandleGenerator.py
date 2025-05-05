from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from ml.data.model.Candle import Candle


class ICandleGenerator(ABC):
    @abstractmethod
    async def generate_candles(self, instrument_id: str, preload_candles_count: int = 0) -> AsyncGenerator[Candle | None, None]:
        pass
