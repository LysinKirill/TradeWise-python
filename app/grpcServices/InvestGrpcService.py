import grpc

from app.debug.ExceptionHandler import exception_handler
from app.domain.models.invest import InstrumentModel
from app.domain.models.invest.InstrumentStatType import InstrumentStatType
from app.domain.models.invest.requests.GetCandlesRequestModel import GetCandlesRequestModel
from app.domain.models.invest.requests.GetInstrumentStatRequestModel import GetInstrumentStatRequestModel
from app.domain.services.IInvestService import IInvestService
from app.infrastructure.JwtAuthorizationDecorator import jwt_authorization
from app.infrastructure.RequestResponseLogging import request_response_logging
from app.proto import invest_pb2, invest_pb2_grpc
import app.domain.services.IClaimValuesService as IClaimValuesService

class InvestGrpcService(invest_pb2_grpc.InvestServiceServicer):
    def __init__(
            self,
            invest_service: IInvestService,
            claim_values_service: IClaimValuesService
    ):
        self.invest_service = invest_service
        self.claim_values_service = claim_values_service

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetSupportedInstruments(self, request, context):
        response = await self.invest_service.get_supported_instruments()
        return invest_pb2.GetSupportedInstrumentsResponse(instruments=
        [InvestGrpcService.__get_instrument_from_model(instrument) for instrument in response.instruments])

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetCandles(self, request, context):
        request_model = GetCandlesRequestModel(
            instrument_id=request.instrument_id,
            from_=getattr(request, "from").ToDatetime() if request.HasField("from") else None,
            to=request.to.ToDatetime() if request.HasField("to") else None
        )
        response = await self.invest_service.get_candles(request_model)
        return invest_pb2.GetCandlesResponse(candles=
        [invest_pb2.Candle(
            timestamp=candle.timestamp,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close
        ) for candle in response.candles])

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetInstrumentStat(self, request, context):
        request_model = GetInstrumentStatRequestModel(
            instrument_id=request.instrument_id,
            stat_type=InvestGrpcService.__get_domain_stat_type(request.stat_type),
            from_=getattr(request, "from").ToDatetime() if request.HasField("from") else None,
            to=request.to.ToDatetime() if request.HasField("to") else None,
        )
        response = await self.invest_service.get_instrument_stat(request_model)

        if response.stat_value is None:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Unable to get value of stat \"{request_model.stat_type.name}\" for instrument \"{request_model.instrument_id}\" for the given period"
            )
            return invest_pb2.GetInstrumentStatResponse()

        return invest_pb2.GetInstrumentStatResponse(stat_value=response.stat_value)

    @staticmethod
    def __get_instrument_from_model(instrument: InstrumentModel.InstrumentModel):
        return invest_pb2.InstrumentInfo(
            id=instrument.id,
            figi={"value" : instrument.figi},
            name=instrument.name,
            lot=instrument.lot,
            currency=instrument.currency,
            sector=instrument.sector,
            buy_available=instrument.buy_available,
            sell_available=instrument.sell_available,
        )

    __proto_to_domain_stat_type_mapping = {
        invest_pb2.StatType.StatType_Unknown: InstrumentStatType.Unknown,
        invest_pb2.StatType.StatType_BollingerBandLower: InstrumentStatType.BollingerBandLower,
        invest_pb2.StatType.StatType_BollingerBandMiddle: InstrumentStatType.BollingerBandMiddle,
        invest_pb2.StatType.StatType_BollingerBandUpper: InstrumentStatType.BollingerBandUpper,
        invest_pb2.StatType.StatType_ExponentialMovingAverage: InstrumentStatType.ExponentialMovingAverage,
        invest_pb2.StatType.StatType_RelativeStrengthIndex: InstrumentStatType.RelativeStrengthIndex,
        invest_pb2.StatType.StatType_MovingAverageConvergenceDivergence: InstrumentStatType.MovingAverageConvergenceDivergence,
        invest_pb2.StatType.StatType_MovingAverage: InstrumentStatType.MovingAverage,
    }
    @staticmethod
    def __get_domain_stat_type(request_stat_type) -> InstrumentStatType:
        return InvestGrpcService\
            .__proto_to_domain_stat_type_mapping\
            .get(request_stat_type, invest_pb2.StatType.StatType_Unknown)
