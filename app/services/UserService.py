from app.domain.models.user.requests.GetAccountsRequestModel import GetAccountsRequestModel
from app.domain.models.user.responses.GetAccountsResponseModel import GetAccountsResponseModel
from app.domain.services.IUserService import IUserService
from externalClients.TInvestApi.handlers.UserClient import UserClient
from app.domain.models.user import (
    AccountTypeModel,
    AccountInfoModel,
    AccountStatusModel,
    AccountAccessLevelModel
)


class UserService(IUserService):
    def __init__(self, user_client: UserClient):
        self.user_client = user_client

    def get_accounts(self, request: GetAccountsRequestModel) -> GetAccountsResponseModel:
        client_response = self.user_client.get_accounts(request.status)
        return GetAccountsResponseModel(
            accounts=list(map(UserService.__get_account, client_response.accounts))
        )

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
