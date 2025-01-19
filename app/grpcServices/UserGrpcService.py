from app.debug.ExceptionLogger import exception_logging
from app.domain.models.user.requests.GetAccountsRequestModel import GetAccountsRequestModel
from app.domain.models.user.AccountStatusModel import AccountStatusModel
from app.infrastructure.RequestResponseLogging import request_response_logging
from app.proto import user_pb2, user_pb2_grpc
import app.domain.services.IUserService as IUserService


class UserGrpcService(user_pb2_grpc.UserServiceServicer):
    def __init__(self, user_service: IUserService):
        self.user_service = user_service

    @exception_logging
    @request_response_logging()
    def GetAccounts(self, request, context):
        request_model = GetAccountsRequestModel(status=UserGrpcService.__get_account_status(request.account_status))
        response = self.user_service.get_accounts(request_model)

        return user_pb2.GetAccountsResponse(accounts=
        [user_pb2.AccountInfo(id=account.id, name=account.name) for account in response.accounts])


    @staticmethod
    def __get_account_status(status) -> AccountStatusModel:
        match status:
            case 0: return AccountStatusModel.ACCOUNT_STATUS_UNSPECIFIED
            case 1: return AccountStatusModel.ACCOUNT_STATUS_NEW
            case 2: return AccountStatusModel.ACCOUNT_STATUS_OPEN
            case 3: return AccountStatusModel.ACCOUNT_STATUS_CLOSED
            case 4: return AccountStatusModel.ACCOUNT_STATUS_ALL
            case _: return AccountStatusModel.ACCOUNT_STATUS_UNSPECIFIED
