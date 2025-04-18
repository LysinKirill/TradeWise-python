from app.debug.ExceptionLogger import exception_logging
from app.domain.models.invest import InstrumentModel
from app.domain.models.invest.InstrumentStatType import InstrumentStatType
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

    @exception_logging
    @request_response_logging()
    @jwt_authorization
    def GetSupportedInstruments(self, request, context):
        response = self.invest_service.get_supported_instruments()
        return invest_pb2.GetSupportedInstrumentsResponse(instruments=
        [InvestGrpcService.__get_instrument_from_model(instrument) for instrument in response.instruments])


    def GetInstrumentStat(self, request, context):
        request_model = GetInstrumentStatRequestModel(
            instrument_id=request.instrument_id,
            stat_type=InvestGrpcService.__get_domain_stat_type(request.stat_type),
            from_=getattr(request, "from").ToDatetime() if request.HasField("from") else None,
            to=request.to.ToDatetime() if request.HasField("to") else None,
        )
        response = self.invest_service.get_instrument_stat(request_model)
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
        invest_pb2.StatType.Unknown: InstrumentStatType.Unknown,
        invest_pb2.StatType.BollingerBandLower: InstrumentStatType.BollingerBandLower,
        invest_pb2.StatType.BollingerBandMiddle: InstrumentStatType.BollingerBandMiddle,
        invest_pb2.StatType.BollingerBandUpper: InstrumentStatType.BollingerBandUpper,
        invest_pb2.StatType.ExponentialMovingAverage: InstrumentStatType.ExponentialMovingAverage,
        invest_pb2.StatType.RelativeStrengthIndex: InstrumentStatType.RelativeStrengthIndex,
        invest_pb2.StatType.MovingAverageConvergenceDivergence: InstrumentStatType.MovingAverageConvergenceDivergence,
        invest_pb2.StatType.MovingAverage: InstrumentStatType.MovingAverage,
    }
    @staticmethod
    def __get_domain_stat_type(request_stat_type) -> InstrumentStatType:
        return InvestGrpcService\
            .__proto_to_domain_stat_type_mapping\
            .get(request_stat_type, invest_pb2.StatType.Unknown)
