from abc import ABC, abstractmethod

from app.domain.models.user.requests import GetAccountsRequestModel
from app.domain.models.user.responses import GetAccountsResponseModel


class IUserService(ABC):
    @abstractmethod
    def get_accounts(self, request: GetAccountsRequestModel) -> GetAccountsResponseModel:
        pass
