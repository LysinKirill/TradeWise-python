import grpc
from datetime import datetime, timedelta, timezone

from app.domain.models.invest.InstrumentStatType import InstrumentStatType
from app.domain.models.invest.requests import GetInstrumentStatRequestModel
from google.protobuf import timestamp_pb2

from externalClients.TInvestApi.handlers.BaseClient import BaseClient
from externalClients.TInvestApi.proto import (
    marketdata_pb2, marketdata_pb2_grpc,
)


class MarketDataClient(BaseClient):
    def __init__(self, endpoint: str, api_key: str):
        super().__init__(endpoint, api_key)
        self.stub = marketdata_pb2_grpc.MarketDataServiceStub(self.channel)


    def get_instrument_stat(self, request: GetInstrumentStatRequestModel.GetInstrumentStatRequestModel):
        indicator_type = MarketDataClient.__python_to_grpc_enum(request.stat_type)

        now = datetime.now(timezone.utc)

        timestamp_from = timestamp_pb2.Timestamp()
        timestamp_from.FromDatetime(
            now - timedelta(minutes=5) if request.from_ is None else request.from_
        )
        timestamp_to = timestamp_pb2.Timestamp()
        timestamp_to.FromDatetime(
            now if request.to is None else request.to
        )

        invest_api_request = marketdata_pb2.GetTechAnalysisRequest(
            indicator_type = indicator_type,
            instrument_uid = request.instrument_id,
            to = timestamp_to,
            from_ = timestamp_from,
            interval = marketdata_pb2.GetTechAnalysisRequest.IndicatorInterval.INDICATOR_INTERVAL_FIVE_MINUTES,
            type_of_price = marketdata_pb2.GetTechAnalysisRequest.TypeOfPrice.TYPE_OF_PRICE_AVG
        )
        setattr(invest_api_request, "from", timestamp_from)

        return self.stub.GetTechAnalysis(invest_api_request, metadata=self.get_metadata())

    @staticmethod
    def __python_to_grpc_enum(python_enum_value):
        """Convert Python enum to gRPC enum"""
        mapping = {
            InstrumentStatType.Unknown: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_UNSPECIFIED,
            InstrumentStatType.BollingerBands: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_BB,
            InstrumentStatType.ExponentialMovingAverage: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_EMA,
            InstrumentStatType.RelativeStrengthIndex: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_RSI,
            InstrumentStatType.MovingAverageConvergenceDivergence: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_MACD,
            InstrumentStatType.MovingAverage: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_SMA,
        }
        return mapping.get(python_enum_value, marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_UNSPECIFIED)