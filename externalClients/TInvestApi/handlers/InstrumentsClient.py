import grpc

from externalClients.TInvestApi.proto import instruments_pb2, instruments_pb2_grpc


class InstrumentsClient:
    def __init__(self, endpoint: str, api_key: str):
        self.channel = grpc.secure_channel(endpoint, grpc.ssl_channel_credentials())
        self.stub = instruments_pb2_grpc.InstrumentsServiceStub(self.channel)
        self.api_key = api_key

    def get_metadata(self):
        return [('authorization', f'Bearer {self.api_key}')]

    def get_instruments(self):
        request = instruments_pb2.InstrumentsRequest()
        response = self.stub.Bonds(request, metadata=self.get_metadata())

        return response

    def close(self):
        self.channel.close()