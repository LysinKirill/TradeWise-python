from externalClients.TInvestApi.handlers.BaseClient import BaseClient
from externalClients.TInvestApi.proto import (
    instruments_pb2, instruments_pb2_grpc,
)


class InstrumentsClient(BaseClient):
    def __init__(self, endpoint: str, api_key: str):
        super().__init__(endpoint, api_key)
        self.stub = instruments_pb2_grpc.InstrumentsServiceStub(self.channel)


    async def get_instruments(self, instrument_ids: list[str]):
        instruments = []
        for instrument_id in instrument_ids:
            request = instruments_pb2.InstrumentRequest(
                id_type = instruments_pb2.InstrumentIdType.Value("INSTRUMENT_ID_TYPE_UID"),
                id = instrument_id
            )
            response = await self.stub.ShareBy(request, metadata=self.get_metadata())
            instruments.append(response.instrument)
        return instruments