from abc import ABC, abstractmethod

from app.domain.models.user.requests import (
    GetAccountsRequestModel,
    AddInvestApiKeyRequestModel
)
from app.domain.models.user.responses import GetAccountsResponseModel


class IUserService(ABC):
    @abstractmethod
    def get_accounts(self, request: GetAccountsRequestModel.GetAccountsRequestModel) -> GetAccountsResponseModel.GetAccountsResponseModel:
        pass

    @abstractmethod
    def add_invest_api_key(self, request: AddInvestApiKeyRequestModel.AddInvestApiKeyRequestModel) -> bool:
        pass