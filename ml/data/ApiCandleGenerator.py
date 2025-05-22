import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from app.domain.models.invest.requests.GetCandlesRequestModel import GetCandlesRequestModel
from app.domain.models.invest.CandleModel import CandleModel
from externalClients.TInvestApi.handlers.MarketDataClient import MarketDataClient
from ml.data.RetryPolicy import RetryPolicy
from ml.data.interface.ICandleGenerator import ICandleGenerator
from datetime import datetime, timezone, timedelta


@dataclass
class _PreloadCandleRequest:
    instrument_id: str
    preload_candles_count: int

class ApiCandleGenerator(ICandleGenerator):
    def __init__(
        self,
        marketdata_client: MarketDataClient,
        fetch_delay_in_seconds: float,
        retry_policy: RetryPolicy,
    ):
        self.marketdata_client = marketdata_client
        self.fetch_delay_in_seconds = fetch_delay_in_seconds
        self.retry_policy = retry_policy

    async def generate_candles(
        self,
        instrument_id: str,
        preload_candles_count: int = 0,
        stop_event: asyncio.Event | None = None
    ) -> AsyncGenerator[CandleModel | None, None]:
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



    async def _attempt_preload_candles(self, request: _PreloadCandleRequest) -> list[CandleModel] | None:
        now = datetime.now(timezone.utc)
        datetime_from = now - timedelta(minutes=request.preload_candles_count + 5)
        datetime_to = now

        last_candles = await self.marketdata_client.get_candles(
            GetCandlesRequestModel(request.instrument_id, datetime_from, datetime_to)
        )

        if last_candles is None or len(last_candles) == 0:
            return None

        return last_candles



    async def _attempt_fetch_candle(self, instrument_id: str) -> CandleModel | None:
        preload_request = _PreloadCandleRequest(
            instrument_id=instrument_id,
            preload_candles_count=1,
        )
        candles = await self._attempt_preload_candles(preload_request)
        if candles is None or len(candles) == 0:
            return None

        return candles[-1]