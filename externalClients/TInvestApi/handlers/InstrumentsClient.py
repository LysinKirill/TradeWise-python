from app.domain.services.IClaimValuesService import IClaimValuesService
from dataAccess.interfaces.IUserRepository import IUserRepository
from externalClients.TInvestApi.handlers.BaseClient import BaseClient
from externalClients.TInvestApi.proto import (
    instruments_pb2, instruments_pb2_grpc,
)


class InstrumentsClient(BaseClient):
    def __init__(
            self,
            endpoint: str,
            claim_values_service: IClaimValuesService,
            user_repository: IUserRepository
    ):
        super().__init__(endpoint, claim_values_service, user_repository)
        self.stub = instruments_pb2_grpc.InstrumentsServiceStub(self.channel)


    async def get_instruments(self, instrument_ids: list[str]):
        instruments = []
        for instrument_id in instrument_ids:
            request = instruments_pb2.InstrumentRequest(
                id_type = instruments_pb2.InstrumentIdType.Value("INSTRUMENT_ID_TYPE_UID"),
                id = instrument_id
            )
            response = await self.stub.ShareBy(request, metadata=await self.get_metadata())
            instruments.append(response.instrument)
        return instruments