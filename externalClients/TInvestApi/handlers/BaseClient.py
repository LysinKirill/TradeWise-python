import grpc


class BaseClient:
    def __init__(self, endpoint: str, api_key: str):
        self.channel = grpc.secure_channel(endpoint, grpc.ssl_channel_credentials())
        self.api_key = api_key

    def get_metadata(self):
        return [('authorization', f'Bearer {self.api_key}')]

    def close(self):
        self.channel.close()