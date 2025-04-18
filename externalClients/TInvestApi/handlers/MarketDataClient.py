import grpc
from datetime import datetime, timedelta, timezone

from app.domain.models.invest.InstrumentStatType import InstrumentStatType
from app.domain.models.invest.requests import GetInstrumentStatRequestModel
from google.protobuf import timestamp_pb2

from externalClients.TInvestApi.handlers.BaseClient import BaseClient
from externalClients.TInvestApi.proto import (
    marketdata_pb2, marketdata_pb2_grpc,
    common_pb2
)


class MarketDataClient(BaseClient):
    def __init__(self, endpoint: str, api_key: str):
        super().__init__(endpoint, api_key)
        self.stub = marketdata_pb2_grpc.MarketDataServiceStub(self.channel)


    def get_instrument_stat(self, request: GetInstrumentStatRequestModel.GetInstrumentStatRequestModel):
        indicator_type = MarketDataClient.__python_to_grpc_enum(request.stat_type)

        now = datetime.now(timezone.utc)
        datetime_from = now - timedelta(minutes=5) if request.from_ is None else request.from_
        datetime_to = now if request.to is None else request.to

        # {
        #     "from": {
        #         "nanos": 756650000,
        #         "seconds": "1744750199"
        #     },
        #     "indicator_type": "INDICATOR_TYPE_MACD",
        #     "instrument_uid": "e6123145-9665-43e0-8413-cd61b8aa9b13",
        #     "interval": "INDICATOR_INTERVAL_ONE_MINUTE",
        #
        #     "smoothing": {
        #         "fast_length": 1,
        #         "signal_smoothing": 2,
        #         "slow_length": 5
        #     },
        #     "to": {
        #         "nanos": 756650000,
        #         "seconds": "1744764782"
        #     },
        #     "type_of_price": "TYPE_OF_PRICE_AVG"
        # }

        deviation = marketdata_pb2.GetTechAnalysisRequest.Deviation(
            deviation_multiplier=common_pb2.Quotation(
                units=2,
                nano=0,
            )
        )

        smoothing = marketdata_pb2.GetTechAnalysisRequest.Smoothing(
            fast_length=1,
            signal_smoothing=2,
            slow_length=5,
        )


        invest_api_request = marketdata_pb2.GetTechAnalysisRequest(
            indicator_type = indicator_type,
            instrument_uid = request.instrument_id,
            to = datetime_to,
            interval = marketdata_pb2.GetTechAnalysisRequest.IndicatorInterval.INDICATOR_INTERVAL_FIVE_MINUTES,
            type_of_price = marketdata_pb2.GetTechAnalysisRequest.TypeOfPrice.TYPE_OF_PRICE_AVG,
            smoothing = smoothing,
            deviation=deviation,
            length=5
        )
        setattr(invest_api_request, "from", datetime_from)

        try:
            invest_api_response = self.stub.GetTechAnalysis(invest_api_request, metadata=self.get_metadata())
        except Exception as e:
            print(e)
            raise

        technical_indicators = invest_api_response.technical_indicators
        if not technical_indicators:
            return None

        last_observation = technical_indicators[-1]

        match request.stat_type:
            case InstrumentStatType.Unknown: return None
            case InstrumentStatType.BollingerBands: return
            case InstrumentStatType.ExponentialMovingAverage: return
            case InstrumentStatType.RelativeStrengthIndex: return
            case InstrumentStatType.MovingAverageConvergenceDivergence: return MarketDataClient.__quotation_to_float(last_observation.macd)
            case InstrumentStatType.MovingAverage: return


        stat = invest_api_response[0]
        if request.stat_type == InstrumentStatType.MovingAverage:
            return stat.middle_band
        if request.stat_type == InstrumentStatType.BollingerBands:
            return stat.bollinger_band

    @staticmethod
    def __python_to_grpc_enum(python_enum_value: InstrumentStatType):
        mapping = {
            InstrumentStatType.Unknown: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_UNSPECIFIED,
            InstrumentStatType.BollingerBands: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_BB,
            InstrumentStatType.ExponentialMovingAverage: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_EMA,
            InstrumentStatType.RelativeStrengthIndex: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_RSI,
            InstrumentStatType.MovingAverageConvergenceDivergence: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_MACD,
            InstrumentStatType.MovingAverage: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_SMA,
        }
        return mapping.get(python_enum_value, marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_UNSPECIFIED)


    NANO_CONVERSION_FACTOR: float = 1e-9
    @staticmethod
    def __quotation_to_float(quotation: common_pb2.Quotation | None) -> float | None:
        if quotation is None:
            return None
        return quotation.units + quotation.nano * MarketDataClient.NANO_CONVERSION_FACTOR
