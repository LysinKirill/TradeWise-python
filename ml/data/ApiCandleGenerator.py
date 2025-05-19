import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from ml.TInvestDataProvider import TInvestDataProvider
from ml.data.RetryPolicy import RetryPolicy
from ml.data.interface.ICandleGenerator import ICandleGenerator
from ml.data.model.Candle import Candle
from datetime import datetime, timezone, timedelta
from externalClients.TInvestApi.proto.marketdata_pb2 import (
    CandleInterval
)


@dataclass
class _PreloadCandleRequest:
    instrument_id: str
    preload_candles_count: int

class ApiCandleGenerator(ICandleGenerator):
    def __init__(
        self,
        data_provider: TInvestDataProvider,
        fetch_delay_in_seconds: float,
        retry_policy: RetryPolicy,
    ):
        self.data_provider = data_provider
        self.fetch_delay_in_seconds = fetch_delay_in_seconds
        self.retry_policy = retry_policy

    async def generate_candles(
        self,
        instrument_id: str,
        preload_candles_count: int = 0,
        stop_event: asyncio.Event | None = None
    ) -> AsyncGenerator[Candle | None, None]:
        preload_request = _PreloadCandleRequest(
            instrument_id=instrument_id,
            preload_candles_count=preload_candles_count,
        )
        preloaded_candles = await self.retry_policy.invoke(self._attempt_preload_candles, preload_request, verbose=True)
        if preloaded_candles is not None:
            for candle in preloaded_candles:
                yield candle

        while not (stop_event and stop_event.is_set()):
            candle = await self.retry_policy.invoke(self._attempt_fetch_candle, instrument_id, verbose=True)
            delay_task = asyncio.create_task(asyncio.sleep(self.fetch_delay_in_seconds))
            yield candle
            try:
                await delay_task
            except asyncio.CancelledError:
                if delay_task and not delay_task.done():
                    delay_task.cancel()
                raise



    async def _attempt_preload_candles(self, request: _PreloadCandleRequest) -> list[Candle] | None:
        now = datetime.now(timezone.utc)
        datetime_from = now - timedelta(minutes=request.preload_candles_count + 5)
        datetime_to = now

        last_candles = await self.data_provider.get_historical_candles(
            instrument_id=request.instrument_id,
            from_time=datetime_from,
            to_time=datetime_to,
            interval=CandleInterval.CANDLE_INTERVAL_1_MIN
        )

        if last_candles is None or len(last_candles) == 0:
            return None

        return list(map(lambda x: Candle(close=x['close'], timestamp=x['time']), last_candles[['close', 'time']].iloc[-request.preload_candles_count:]))



    async def _attempt_fetch_candle(self, instrument_id: str) -> Candle | None:
        preload_request = _PreloadCandleRequest(
            instrument_id=instrument_id,
            preload_candles_count=1,
        )
        candles = await self._attempt_preload_candles(preload_request)
        if candles is None or len(candles) == 0:
            return None

        return candles[-1]