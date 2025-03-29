import grpc

from app.domain.models.user import AccountStatusModel
from externalClients.TInvestApi.proto import users_pb2, users_pb2_grpc


class UserClient:
    def __init__(self, endpoint: str, api_key: str):
        self.channel = grpc.secure_channel(endpoint, grpc.ssl_channel_credentials())
        self.stub = users_pb2_grpc.UsersServiceStub(self.channel)
        self.api_key = api_key

    def get_metadata(self):
        return [('authorization', f'Bearer {self.api_key}')]

    def get_accounts(self, account_status: AccountStatusModel.AccountStatusModel =
                     AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_ALL):
        request = users_pb2.GetAccountsRequest(status=UserClient.__get_client_account_status(account_status))
        response = self.stub.GetAccounts(request, metadata=self.get_metadata())

        return response

    def close(self):
        self.channel.close()

    @staticmethod
    def __get_client_account_status(account_status: AccountStatusModel.AccountStatusModel) -> users_pb2.AccountStatus:
        match account_status:
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_UNSPECIFIED: return 0
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_NEW: return 1
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_OPEN: return 2
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_CLOSED: return 3
            case AccountStatusModel.AccountStatusModel.ACCOUNT_STATUS_ALL: return 4
            case _: return 0