from app.debug.ExceptionLogger import exception_logging
from app.domain.models.invest import InstrumentModel
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