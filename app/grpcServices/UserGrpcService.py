from app.proto import user_pb2, user_pb2_grpc
import app.domain.services.IUserService as IUserService


class UserGrpcService(user_pb2_grpc.UserServiceServicer):
    def __init__(self, user_service: IUserService):
        self.user_service = user_service

    def GetAccounts(self, request, context):
        response: str = self.user_service.get_accounts()
        return user_pb2.GetAccountsResponse(accounts=response)