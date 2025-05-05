import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime

from ml.TInvestDataProvider import TInvestDataProvider
from ml.data.interface.ICandleGenerator import ICandleGenerator
from ml.data.model.Candle import Candle


class HistoryCandleGenerator(ICandleGenerator):
    def __init__(
            self,
            invest_api_key: str,
            start_timestamp: datetime,
            end_timestamp: datetime,
            instrument_id: str,
    ):
        self.candle_data = None
        self.invest_api_key = invest_api_key
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.instrument_id = instrument_id

    async def load_data(
            self,
    ) -> None:
        provider = TInvestDataProvider(api_key=self.invest_api_key)
        df = await provider.load_candle_data_for_period(
            period_start_utc=self.start_timestamp,
            period_end_utc=self.end_timestamp,
            instrument_id=self.instrument_id
        )
        await provider.close()
        self.candle_data = [Candle(close=x.close, timestamp=x.time) for x in df[['close', 'time']].itertuples()]


    async def generate_candles(
        self,
        instrument_id: str,
        preload_candles_count: int = 0,
        stop_event: asyncio.Event | None = None
    ) -> AsyncGenerator[Candle | None, None]:
        await self.load_data()

        for candle in self.candle_data:
            yield candle