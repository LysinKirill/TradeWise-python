import grpc

from externalClients.TInvestApi.proto import users_pb2, users_pb2_grpc
from app.domain.models.user import AccountStatusModel


class UserClient:
    def __init__(self, endpoint: str, token: str):
        self.channel = grpc.secure_channel(endpoint, grpc.ssl_channel_credentials())
        self.stub = users_pb2_grpc.UsersServiceStub(self.channel)
        self.token = token

    def get_metadata(self):
        return [('authorization', f'Bearer {self.token}')]

    def get_accounts(self, account_status: AccountStatusModel.AccountStatusModel):
        request = users_pb2.GetAccountsRequest(
            status=UserClient.__get_client_account_status(account_status))
        response = self.stub.GetAccounts(request, metadata=self.get_metadata())
        return response

    def close(self):
        self.channel.close()

    @staticmethod
    def __get_client_account_status(account_status: AccountStatusModel.AccountStatusModel) -> users_pb2.AccountStatus:
        raise NotImplementedError()


