from grpc import aio, ssl_channel_credentials

from app.domain.exceptions.user.InvestApiKeyNotSetException import InvestApiKeyNotSetException
from app.domain.exceptions.user.UserNotFoundException import UserNotFoundException
from app.domain.services.IClaimValuesService import IClaimValuesService
from dataAccess.interfaces.IUserRepository import IUserRepository
from externalClients.TInvestApi.proto import (common_pb2)


class BaseClient:
    def __init__(
            self,
            endpoint: str,
            claim_values_service: IClaimValuesService,
            user_repository: IUserRepository
    ):
        self.channel = aio.secure_channel(endpoint, ssl_channel_credentials())
        self.claim_values_service = claim_values_service
        self.user_repository = user_repository

    async def get_metadata(self):
        user_email = await self.claim_values_service.get_email()
        user = await self.user_repository.get_user_by_email(user_email)
        if user is None:
            raise UserNotFoundException(user_email)

        if user.invest_api_key is None:
            raise InvestApiKeyNotSetException(user.id)

        return [('authorization', f'Bearer {user.invest_api_key}')]

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