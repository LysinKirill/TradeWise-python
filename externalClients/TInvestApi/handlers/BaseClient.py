from grpc import aio, ssl_channel_credentials


class BaseClient:
    def __init__(self, endpoint: str, api_key: str):
        self.channel = aio.secure_channel(endpoint, ssl_channel_credentials())
        self.api_key = api_key

    def get_metadata(self):
        return [('authorization', f'Bearer {self.api_key}')]

    async def close(self):
        await self.channel.close()