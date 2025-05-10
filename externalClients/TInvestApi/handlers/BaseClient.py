from grpc import aio, ssl_channel_credentials
from externalClients.TInvestApi.proto import (common_pb2)


class BaseClient:
    def __init__(self, endpoint: str, api_key: str):
        self.channel = aio.secure_channel(endpoint, ssl_channel_credentials())
        self.api_key = api_key

    def get_metadata(self):
        return [('authorization', f'Bearer {self.api_key}')]

    async def close(self):
        await self.channel.close()



    NANO_CONVERSION_FACTOR: float = 1e-9
    @staticmethod
    def _quotation_to_float(quotation: common_pb2.Quotation | None) -> float | None:
        if quotation is None:
            return None
        return quotation.units + quotation.nano * BaseClient.NANO_CONVERSION_FACTOR

    @staticmethod
    def _money_to_float(money: common_pb2.MoneyValue | None) -> float | None:
        if money is None:
            return None
        return money.units + money.nano * BaseClient.NANO_CONVERSION_FACTOR