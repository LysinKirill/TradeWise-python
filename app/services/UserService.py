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
            type=UserService.__get_account_type(client_account.account_type),
            name=client_account.name,
            status=UserService.__get_account_status(client_account.account_status),
            opened_date=client_account.opened_date.ToDatetime(),
            closed_date=client_account.closed_date.ToDatetime(),
            access_level=UserService.__get_account_access_level(client_account.access_level)
        )

    @staticmethod
    def __get_account_type(client_account_type) -> AccountTypeModel.AccountTypeModel:
        match client_account_type:
            # add cases for matching
            case _: raise NotImplementedError("Account type mapping is not implemented.")
        pass

    @staticmethod
    def __get_account_status(client_account_status) -> AccountStatusModel.AccountStatusModel:
        match client_account_status:
            # add cases for matching
            case _: raise NotImplementedError("Account status mapping is not implemented.")
        pass

    @staticmethod
    def __get_account_access_level(client_account_access_level) -> AccountAccessLevelModel.AccountAccessLevelModel:
        match client_account_access_level:
            # add cases for matching
            case _: raise NotImplementedError("Account access level mapping is not implemented.")
        pass

