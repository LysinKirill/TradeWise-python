import pandas as pd
import asyncio

from datetime import datetime, timedelta
from typing import Optional, List
from grpc import aio, ssl_channel_credentials
from google.protobuf.timestamp_pb2 import Timestamp


import instruments_pb2
import instruments_pb2_grpc
from externalClients.TInvestApi.proto import marketdata_pb2_grpc
from externalClients.TInvestApi.proto.marketdata_pb2 import (
    GetCandlesRequest,
    GetCandlesResponse,
    HistoricCandle,
    CandleInterval,
    MarketDataRequest,
    MarketDataResponse,
    SubscribeCandlesRequest,
    SubscriptionAction,
    SubscriptionInterval
)

from externalClients.TInvestApi.proto.instruments_pb2 import (
    InstrumentRequest,
    InstrumentIdType
)

class TInvestDataProvider:
    def __init__(self, api_key: str, prod_endpoint: str = "invest-public-api.tinkoff.ru:443"):
        self.api_key = api_key
        self.endpoint = prod_endpoint
        self.channel = None
        self.marketdata_stub = None
        self.instruments_stub = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize gRPC connection and stub."""
        credentials = ssl_channel_credentials()
        self.channel = aio.secure_channel(self.endpoint, credentials)
        self.marketdata_stub = marketdata_pb2_grpc.MarketDataServiceStub(self.channel)
        self.instruments_stub = instruments_pb2_grpc.InstrumentsServiceStub(self.channel)

    def _get_metadata(self):
        """Get authorization metadata for gRPC calls."""
        return [('authorization', f'Bearer {self.api_key}')]

    async def close(self):
        """Close the gRPC channel."""
        if self.channel:
            await self.channel.close()

    def _convert_quotation_to_float(self, quotation) -> float:
        """Convert Tinkoff Quotation type to float."""
        return float(quotation.units + quotation.nano / 1e9)

    def _convert_timestamp_to_datetime(self, timestamp) -> datetime:
        """Convert protobuf Timestamp to Python datetime."""
        return datetime.utcfromtimestamp(timestamp.seconds + timestamp.nanos / 1e9)

    async def get_historical_candles(
        self,
        instrument_id: str,
        from_time: datetime,
        to_time: datetime,
        interval: CandleInterval,
        candle_source_type: Optional[int] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get historical candles for specified instrument and time range.

        Args:
            instrument_id: FIGI or instrument_uid
            from_time: Start time of the period
            to_time: End time of the period
            interval: Candle interval (see CandleInterval enum)
            candle_source_type: Optional candle source type
            limit: Optional maximum number of candles

        Returns:
            Pandas DataFrame with historical candles
        """
        # Convert datetime to protobuf Timestamp
        to_ts = Timestamp()
        to_ts.FromDatetime(to_time)

        # Create request
        request = GetCandlesRequest(
            instrument_id=instrument_id,
            to=to_ts,
            interval=interval,
            candle_source_type=candle_source_type,
            limit=limit
        )
        setattr(request, "from", from_time)

        # Make API call
        response: GetCandlesResponse = await self.marketdata_stub.GetCandles(
            request,
            metadata=self._get_metadata()
        )

        # Process candles into DataFrame
        candles = []
        for candle in response.candles:
            candles.append({
                'time': self._convert_timestamp_to_datetime(candle.time),
                'open': self._convert_quotation_to_float(candle.open),
                'high': self._convert_quotation_to_float(candle.high),
                'low': self._convert_quotation_to_float(candle.low),
                'close': self._convert_quotation_to_float(candle.close),
                'volume': candle.volume,
                'is_complete': candle.is_complete,
                'source': candle.candle_source
            })

        return pd.DataFrame(candles).set_index('time')

    async def subscribe_to_candles(
        self,
        instrument_ids: List[str],
        interval: SubscriptionInterval,
        callback: callable
    ) -> None:
        """
        Subscribe to real-time candle updates.

        Args:
            instrument_ids: List of instrument IDs to subscribe to
            interval: Subscription interval (see SubscriptionInterval enum)
            callback: Function to call when new data arrives
        """
        # Create subscription requests
        subscription_list = [
            SubscribeCandlesRequest(
                subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                instruments=[
                    SubscribeCandlesRequest.CandleInstrument(
                        instrument_id=inst_id,
                        interval=interval
                    )
                    for inst_id in instrument_ids
                ]
            )
        ]

        # Create market data request
        request = MarketDataRequest(
            subscribe_candles_request=subscription_list
        )

        # Start streaming
        async for response in self.marketdata_stub.MarketDataStream(
            iter([request]),
            metadata=self._get_metadata()
        ):
            if response.HasField('candle'):
                candle_data = {
                    'time': self._convert_timestamp_to_datetime(response.candle.time),
                    'open': self._convert_quotation_to_float(response.candle.open),
                    'high': self._convert_quotation_to_float(response.candle.high),
                    'low': self._convert_quotation_to_float(response.candle.low),
                    'close': self._convert_quotation_to_float(response.candle.close),
                    'volume': response.candle.volume,
                    'is_complete': response.candle.is_complete,
                    'instrument_id': response.candle.figi
                }
                await callback(candle_data)



    DEFAULT_RATE_LIMITER_DELAY = 0.25
    DEFAULT_CANDLE_COUNT = 100_000

    async def load_candle_data(
        self,
        train_period_end_utc: datetime,
        instrument_id: str,
        target_candle_count: int = DEFAULT_CANDLE_COUNT,
        rate_limiter_delay_seconds: float = DEFAULT_RATE_LIMITER_DELAY
    ) -> pd.DataFrame:
        timestep = timedelta(hours=40)

        df = None
        current_end = train_period_end_utc
        current_start = current_end - timestep
        step_count = 1

        try:
            while True:
                print(f"Step {step_count}. ", end="")
                step_count += 1
                current_start = current_end - timestep

                new_df = await self.get_historical_candles(
                    instrument_id="e6123145-9665-43e0-8413-cd61b8aa9b13",
                    from_time=current_start,
                    to_time=current_end,
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN
                )

                if df is None:
                    df = new_df
                else:
                    df = pd.concat([new_df, df])

                if len(df) >= target_candle_count:
                    df = df.iloc[-target_candle_count:]
                    print(f"Current df shape: {df.shape}")
                    break

                current_end = current_start
                print(f"Current df shape: {df.shape}; new candles fetched = {new_df.shape[0]}")
                await asyncio.sleep(rate_limiter_delay_seconds)
        except Exception as e:
            print(f"Unable to fetch data {e}")
            last_request_sent = {
                "instrument_id": instrument_id,
                "from_time": current_start,
                "to_time": current_end,
                "interval": CandleInterval.CANDLE_INTERVAL_1_MIN
            }
            print(f"Last executed request: {last_request_sent}")

        return df

    async def get_instrument_info(self, instrument_id: str):
        request = InstrumentRequest(
            id_type=InstrumentIdType.Value("INSTRUMENT_ID_TYPE_UID"),
            id=instrument_id
        )
        response = await self.instruments_stub.ShareBy(request, metadata=self._get_metadata())
        return response.instrument

    async def load_candle_data_for_period(
        self,
        period_start_utc: datetime,
        period_end_utc: datetime,
        instrument_id: str,
        rate_limiter_delay_seconds: float = DEFAULT_RATE_LIMITER_DELAY
    ) -> pd.DataFrame:
        timestep = timedelta(hours=40)

        df = None
        current_end = period_end_utc
        current_start = current_end - timestep
        flag = True

        try:
            while flag:
                if current_start < period_start_utc:
                    current_start = period_start_utc
                    flag = False
                current_start = current_end - timestep
                print(f"Fetching data for interval {current_start} - {current_end}. ", end="")

                new_df = await self.get_historical_candles(
                    instrument_id="e6123145-9665-43e0-8413-cd61b8aa9b13",
                    from_time=current_start,
                    to_time=current_end,
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN
                )

                if df is None:
                    df = new_df
                else:
                    df = pd.concat([new_df, df])

                current_end = current_start
                print(f"Current df shape: {df.shape}; new candles fetched = {new_df.shape[0]}\n")
                await asyncio.sleep(rate_limiter_delay_seconds)
        except Exception as e:
            print(f"Unable to fetch data {e}")
            last_request_sent = {
                "instrument_id": instrument_id,
                "from_time": current_start,
                "to_time": current_end,
                "interval": CandleInterval.CANDLE_INTERVAL_1_MIN
            }
            print(f"Last executed request: {last_request_sent}")
        finally:
            await self.close()

        return df