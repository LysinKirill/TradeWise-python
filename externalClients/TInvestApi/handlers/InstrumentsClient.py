import grpc

from externalClients.TInvestApi.proto import instruments_pb2, instruments_pb2_grpc


class InstrumentsClient:
    def __init__(self, endpoint: str, api_key: str):
        self.channel = grpc.secure_channel(endpoint, grpc.ssl_channel_credentials())
        self.stub = instruments_pb2_grpc.InstrumentsServiceStub(self.channel)
        self.api_key = api_key

    def get_metadata(self):
        return [('authorization', f'Bearer {self.api_key}')]

    def get_instruments(self, instrument_ids: list[str]):
        instruments = []
        for instrument_id in instrument_ids:
            request = instruments_pb2.InstrumentRequest(
                id_type = instruments_pb2.InstrumentIdType.Value("INSTRUMENT_ID_TYPE_UID"),
                id = instrument_id
            )
            response = self.stub.ShareBy(request, metadata=self.get_metadata())
            instruments.append(response.instrument)
        return instruments

    def close(self):
        self.channel.close()