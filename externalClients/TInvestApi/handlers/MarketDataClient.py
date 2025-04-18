from datetime import datetime, timedelta, timezone

from app.domain.models.invest.InstrumentStatType import InstrumentStatType
from app.domain.models.invest.requests import GetInstrumentStatRequestModel
from externalClients.TInvestApi.handlers.BaseClient import BaseClient
from externalClients.TInvestApi.proto import (
    marketdata_pb2, marketdata_pb2_grpc,
    common_pb2
)


class MarketDataClient(BaseClient):
    def __init__(self, endpoint: str, api_key: str):
        super().__init__(endpoint, api_key)
        self.stub = marketdata_pb2_grpc.MarketDataServiceStub(self.channel)


    def get_instrument_stat(self, request: GetInstrumentStatRequestModel.GetInstrumentStatRequestModel) -> float | None:
        if request.stat_type == InstrumentStatType.Unknown: return None

        indicator_type = MarketDataClient.__python_to_grpc_enum(request.stat_type)

        now = datetime.now(timezone.utc)
        datetime_from = now - timedelta(minutes=5) if request.from_ is None else request.from_
        datetime_to = now if request.to is None else request.to

        invest_api_request = marketdata_pb2.GetTechAnalysisRequest(
            indicator_type=indicator_type,
            instrument_uid=request.instrument_id,
            to=datetime_to,
            interval=marketdata_pb2.GetTechAnalysisRequest.IndicatorInterval.INDICATOR_INTERVAL_FIVE_MINUTES,
            type_of_price=marketdata_pb2.GetTechAnalysisRequest.TypeOfPrice.TYPE_OF_PRICE_AVG,
            smoothing=MarketDataClient.__default_smoothing,
            deviation=MarketDataClient.__default_deviation,
            length=5
        )
        setattr(invest_api_request, "from", datetime_from)

        invest_api_response = self.stub.GetTechAnalysis(invest_api_request, metadata=self.get_metadata())

        technical_indicators = invest_api_response.technical_indicators
        if not technical_indicators:
            return None

        last_observation = technical_indicators[-1]

        match request.stat_type:
            case InstrumentStatType.BollingerBandLower: return MarketDataClient.__quotation_to_float(last_observation.lower_band)
            case InstrumentStatType.BollingerBandMiddle: return MarketDataClient.__quotation_to_float(last_observation.middle_band)
            case InstrumentStatType.BollingerBandUpper: return MarketDataClient.__quotation_to_float(last_observation.upper_band)
            case InstrumentStatType.ExponentialMovingAverage: return MarketDataClient.__quotation_to_float(last_observation.signal)
            case InstrumentStatType.RelativeStrengthIndex: return MarketDataClient.__quotation_to_float(last_observation.signal)
            case InstrumentStatType.MovingAverageConvergenceDivergence: return MarketDataClient.__quotation_to_float(last_observation.macd)
            case InstrumentStatType.MovingAverage: return MarketDataClient.__quotation_to_float(last_observation.signal)
            case _: return None


    __domain_to_client_stat_type_mapping = {
        InstrumentStatType.Unknown: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_UNSPECIFIED,
        InstrumentStatType.BollingerBandLower: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_BB,
        InstrumentStatType.BollingerBandMiddle: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_BB,
        InstrumentStatType.BollingerBandUpper: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_BB,
        InstrumentStatType.ExponentialMovingAverage: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_EMA,
        InstrumentStatType.RelativeStrengthIndex: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_RSI,
        InstrumentStatType.MovingAverageConvergenceDivergence: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_MACD,
        InstrumentStatType.MovingAverage: marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_SMA,
    }
    @staticmethod
    def __python_to_grpc_enum(python_enum_value: InstrumentStatType):
        return MarketDataClient\
            .__domain_to_client_stat_type_mapping\
            .get(python_enum_value, marketdata_pb2.GetTechAnalysisRequest.IndicatorType.INDICATOR_TYPE_UNSPECIFIED)


    NANO_CONVERSION_FACTOR: float = 1e-9
    @staticmethod
    def __quotation_to_float(quotation: common_pb2.Quotation | None) -> float | None:
        if quotation is None:
            return None
        return quotation.units + quotation.nano * MarketDataClient.NANO_CONVERSION_FACTOR


    __default_deviation = marketdata_pb2.GetTechAnalysisRequest.Deviation(
        deviation_multiplier=common_pb2.Quotation(
            units=2,
            nano=0,
        )
    )

    __default_smoothing = marketdata_pb2.GetTechAnalysisRequest.Smoothing(
        fast_length=1,
        signal_smoothing=2,
        slow_length=5,
    )
