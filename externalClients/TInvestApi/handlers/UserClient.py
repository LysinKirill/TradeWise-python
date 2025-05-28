import grpc

from app.domain.exceptions.user.NoAccountsExistException import NoAccountsExistException
from app.domain.models.user import AccountStatusModel
from app.domain.services.IClaimValuesService import IClaimValuesService
from dataAccess.interfaces.IUserRepository import IUserRepository
from externalClients.TInvestApi.handlers.BaseClient import BaseClient
from externalClients.TInvestApi.proto import users_pb2, users_pb2_grpc


class UserClient(BaseClient):
    def __init__(
            self,
            endpoint: str,
            claim_values_service: IClaimValuesService,
            user_repository: IUserRepository
    ):
        super().__init__(endpoint, claim_values_service, user_repository)
        self.stub = users_pb2_grpc.UsersServiceStub(self.channel)

    async def get_accounts(self, account_status: AccountStatusModel.AccountStatusModel =
                     AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_ALL):
        request = users_pb2.GetAccountsRequest(status=UserClient.__get_client_account_status(account_status))
        response = await self.stub.GetAccounts(request, metadata=await self.get_metadata())
        return response

    async def get_active_account_with_token(
            self,
            token: str
    ):
        request = users_pb2.GetAccountsRequest(status=UserClient.__get_client_account_status(AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_OPEN))
        try:
            response = await self.stub.GetAccounts(request, metadata=[('authorization', f'Bearer {token}')])
            return response
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                raise NoAccountsExistException("No invest accounts for user found.")
            raise


    @staticmethod
    def __get_client_account_status(account_status: AccountStatusModel.AccountStatusModel) -> users_pb2.AccountStatus:
        match account_status:
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_UNSPECIFIED: return 0
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_NEW: return 1
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_OPEN: return 2
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_CLOSED: return 3
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_ALL: return 4
            case _: return 0