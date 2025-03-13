from app.domain.models.user.responses.GetAccountsResponseModel import GetAccountsResponseModel
from app.domain.services.IUserService import IUserService
from dataAccess.interfaces.IUserRepository import IUserRepository

from externalClients.TInvestApi.handlers.UserClient import UserClient

from app.domain.models.user.requests import (
    AddInvestApiKeyRequestModel,
    GetAccountsRequestModel
)
from app.domain.models.user import (
    AccountTypeModel,
    AccountInfoModel,
    AccountStatusModel,
    AccountAccessLevelModel
)


class UserService(IUserService):
    def __init__(
            self,
            user_client: UserClient,
            user_repository: IUserRepository
    ):
        self.user_client = user_client
        self.user_repository = user_repository

    def get_accounts(self, request: GetAccountsRequestModel.GetAccountsRequestModel) -> GetAccountsResponseModel:
        client_response = self.user_client.get_accounts(request.status)
        return GetAccountsResponseModel(
            accounts=list(map(UserService.__get_account, client_response.accounts))
        )

    def add_invest_api_key(self, request: AddInvestApiKeyRequestModel.AddInvestApiKeyRequestModel) -> bool:
        return self.user_repository.add_invest_api_key(email=request.email, api_key=request.api_key)

    @staticmethod
    def __get_account(client_account) -> AccountInfoModel.AccountInfoModel:
        return AccountInfoModel.AccountInfoModel(
            id=client_account.id,
            type=UserService.__get_account_type(client_account.type),
            name=client_account.name,
            status=UserService.__get_account_status(client_account.status),
            opened_date=client_account.opened_date.ToDatetime(),
            closed_date=client_account.closed_date.ToDatetime(),
            access_level=UserService.__get_account_access_level(client_account.access_level)
        )

    @staticmethod
    def __get_account_type(client_account_type) -> AccountTypeModel.AccountTypeModel:
        return AccountTypeModel.AccountTypeModel(client_account_type)

    @staticmethod
    def __get_account_status(client_account_status) -> AccountStatusModel.AccountStatusModel:
        return AccountStatusModel.AccountStatusModel(client_account_status)

    @staticmethod
    def __get_account_access_level(client_account_access_level) -> AccountAccessLevelModel.AccountAccessLevelModel:
        return AccountAccessLevelModel.AccountAccessLevelModel(client_account_access_level)
