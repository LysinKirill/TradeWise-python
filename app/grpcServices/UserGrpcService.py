from app.debug.ExceptionLogger import exception_handler
from app.domain.exceptions.user.NoAccountsExistException import NoAccountsExistException
from app.domain.models.user.requests.AddInvestApiKeyRequestModel import AddInvestApiKeyRequestModel
from app.domain.models.user.requests.GetAccountsRequestModel import GetAccountsRequestModel
from app.domain.models.user.AccountStatusModel import AccountStatusModel
from app.infrastructure.JwtAuthorizationDecorator import jwt_authorization
from app.infrastructure.RequestResponseLogging import request_response_logging
from app.proto import user_pb2, user_pb2_grpc
from google.protobuf import empty_pb2
import app.domain.services.IUserService as IUserService
import app.domain.services.IClaimValuesService as IClaimValuesService
import grpc


class UserGrpcService(user_pb2_grpc.UserServiceServicer):
    def __init__(
            self,
            user_service: IUserService,
            claim_values_service: IClaimValuesService
    ):
        self.user_service = user_service
        self.claim_values_service = claim_values_service


    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetAccounts(self, request, context):

        request_model = GetAccountsRequestModel(status=UserGrpcService.__get_account_status(request.account_status))
        response = await self.user_service.get_accounts(request_model)

        return user_pb2.GetAccountsResponse(accounts=
        [user_pb2.AccountInfo(id=account.id, name=account.name) for account in response.accounts])

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def AddInvestApiKey(self, request, context):
        email = await self.claim_values_service.get_email()
        request_model = AddInvestApiKeyRequestModel(api_key=request.api_key, email=email)
        try:
            await self.user_service.add_invest_api_key(request_model)
        except NoAccountsExistException:
            # Do not specify explicit reason of failure for security reasons
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'Invalid API key provided.')
        return empty_pb2.Empty()

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetPortfolio(self, request, context):
        portfolio = await self.user_service.get_portfolio()
        return user_pb2.GetPortfolioResponse(
            ruble_balance=portfolio.ruble_balance,
            positions=[
                user_pb2.Position(
                    instrument_id=position.instrument_id,
                    quantity=position.quantity,
                    current_price=position.current_price,
                    ticker=position.ticker,
                    daily_yield=position.daily_yield
                ) for position in portfolio.positions
            ]
        )

    @staticmethod
    def __get_account_status(status) -> AccountStatusModel:
        match status:
            case 0: return AccountStatusModel.ACCOUNT_STATUS_UNSPECIFIED
            case 1: return AccountStatusModel.ACCOUNT_STATUS_NEW
            case 2: return AccountStatusModel.ACCOUNT_STATUS_OPEN
            case 3: return AccountStatusModel.ACCOUNT_STATUS_CLOSED
            case 4: return AccountStatusModel.ACCOUNT_STATUS_ALL
            case _: return AccountStatusModel.ACCOUNT_STATUS_UNSPECIFIED
