from abc import ABC, abstractmethod

from app.domain.models.user.requests import (
    GetAccountsRequestModel,
    AddInvestApiKeyRequestModel
)
from app.domain.models.user.responses import GetAccountsResponseModel


class IUserService(ABC):
    @abstractmethod
    async def get_accounts(self, request: GetAccountsRequestModel.GetAccountsRequestModel) -> GetAccountsResponseModel.GetAccountsResponseModel:
        pass

    @abstractmethod
    async def add_invest_api_key(self, request: AddInvestApiKeyRequestModel.AddInvestApiKeyRequestModel) -> bool:
        pass