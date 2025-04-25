from datetime import datetime, timedelta
from typing import Optional, List, Dict, Union
import pandas as pd
from grpc import aio, ssl_channel_credentials
from google.protobuf.timestamp_pb2 import Timestamp
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

class TInvestDataProvider:
    def __init__(self, api_key: str, prod_endpoint: str = "invest-public-api.tinkoff.ru:443"):
        """
        Initialize Tinkoff Invest API data provider.

        Args:
            api_key: Your Tinkoff Invest API token
            prod_endpoint: API endpoint (default is production)
        """
        self.api_key = api_key
        self.endpoint = prod_endpoint
        self.channel = None
        self.stub = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize gRPC connection and stub."""
        credentials = ssl_channel_credentials()
        self.channel = aio.secure_channel(self.endpoint, credentials)
        self.stub = marketdata_pb2_grpc.MarketDataServiceStub(self.channel)

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
        response: GetCandlesResponse = await self.stub.GetCandles(
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
        async for response in self.stub.MarketDataStream(
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

    async def get_last_n_candles(
        self,
        instrument_id: str,
        interval: CandleInterval,
        n_candles: int,
        candle_source_type: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get last N candles for specified instrument.

        Args:
            instrument_id: FIGI or instrument_uid
            interval: Candle interval
            n_candles: Number of candles to retrieve
            candle_source_type: Optional candle source type

        Returns:
            Pandas DataFrame with last N candles
        """
        # Calculate time range based on interval
        now = datetime.utcnow()

        # Estimate time range needed (approximate)
        interval_mapping = {
            CandleInterval.CANDLE_INTERVAL_1_MIN: timedelta(minutes=n_candles),
            CandleInterval.CANDLE_INTERVAL_5_MIN: timedelta(minutes=5*n_candles),
            CandleInterval.CANDLE_INTERVAL_15_MIN: timedelta(minutes=15*n_candles),
            CandleInterval.CANDLE_INTERVAL_HOUR: timedelta(hours=n_candles),
            CandleInterval.CANDLE_INTERVAL_DAY: timedelta(days=n_candles),
        }

        from_time = now - interval_mapping.get(interval, timedelta(days=n_candles))

        return await self.get_historical_candles(
            instrument_id=instrument_id,
            from_time=from_time,
            to_time=now,
            interval=interval,
            candle_source_type=candle_source_type,
            limit=n_candles
        )
