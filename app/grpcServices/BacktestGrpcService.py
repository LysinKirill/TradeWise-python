from google.protobuf import empty_pb2
from app.debug.ExceptionHandler import exception_handler
from app.domain.models.backtest.BacktestModel import BacktestModel
from app.domain.models.backtest.BacktestStatusModel import BacktestStatusModel
from app.domain.models.backtest.requests.EnqueueBacktestRequestModel import EnqueueBacktestRequestModel
from app.domain.models.user.UserInfoModel import UserInfoModel
from app.domain.services.IBacktestService import IBacktestService
from app.domain.services.IClaimValuesService import IClaimValuesService
from app.infrastructure.JwtAuthorizationDecorator import jwt_authorization
from app.infrastructure.RequestResponseLogging import request_response_logging
from app.proto import backtest_pb2, backtest_pb2_grpc


class BacktestGrpcService(backtest_pb2_grpc.BacktestServiceServicer):
    def __init__(
        self,
        claim_values_service: IClaimValuesService,
        backtest_service: IBacktestService
    ):
        self.claim_values_service = claim_values_service
        self.backtest_service = backtest_service

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def StartBacktest(self, request, context):
        user_email = await self.claim_values_service.get_email()
        enqueue_result = await self.backtest_service.enqueue_backtest(
            EnqueueBacktestRequestModel(
                user_email=user_email,
                model_id=request.model_id,
                from_=request.from_.ToDatetime(),
                to=request.to.ToDatetime(),
                initial_balance=request.initial_balance
            )
        )

        return backtest_pb2.StartBacktestResponse(backtest_id=enqueue_result.backtest_id)

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetBacktestStatus(self, request, context):
        backtest_status = await self.backtest_service.get_backtest_status(request.backtest_id)
        return backtest_pb2.GetBacktestStatusResponse(
            status=BacktestGrpcService._get_grpc_backtest_status(backtest_status)
        )

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetBacktest(self, request, context):
        backtest = await self.backtest_service.get_backtest(request.backtest_id)
        return BacktestGrpcService._get_grpc_backtest(backtest)

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def CancelBacktest(self, request, context):
        await self.backtest_service.cancel_backtest(request.backtest_id)
        return empty_pb2.Empty()

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetAllUserBacktests(self, request, context):
        response = await self.backtest_service.get_backtests_for_user()
        return backtest_pb2.GetAllUserBacktestsResponse(
            backtests=list(map(BacktestGrpcService._get_grpc_backtest, response.backtests))
        )

    @staticmethod
    def _get_grpc_backtest_status(domain_backtest_status: BacktestStatusModel):
        match domain_backtest_status:
            case BacktestStatusModel.UNKNOWN: return backtest_pb2.BacktestStatus.BacktestStatus_Unknown
            case BacktestStatusModel.PENDING: return backtest_pb2.BacktestStatus.BacktestStatus_Pending
            case BacktestStatusModel.FAILED: return backtest_pb2.BacktestStatus.BacktestStatus_Failed
            case BacktestStatusModel.RUNNING: return backtest_pb2.BacktestStatus.BacktestStatus_Running
            case BacktestStatusModel.COMPLETED: return backtest_pb2.BacktestStatus.BacktestStatus_Completed
            case BacktestStatusModel.CANCELLED: return backtest_pb2.BacktestStatus.BacktestStatus_Cancelled

        return backtest_pb2.BacktestStatus.BacktestStatus_Unknown

    @staticmethod
    def _get_grpc_user(domain_user: UserInfoModel):
        return backtest_pb2.UserInfo(
            id=domain_user.id,
            email=domain_user.email,
        )

    @staticmethod
    def _get_grpc_backtest(domain_backtest: BacktestModel):
        return backtest_pb2.BacktestInfo(
            backtest_id=domain_backtest.id,
            user_info=BacktestGrpcService._get_grpc_user(domain_backtest.user_info),
            started_at=domain_backtest.started_at,
            finished_at=domain_backtest.finished_at,
            test_period_start=domain_backtest.test_period_start,
            test_period_end=domain_backtest.test_period_end,
            status=BacktestGrpcService._get_grpc_backtest_status(domain_backtest.status),
            profit=domain_backtest.profit,
            trades_count=domain_backtest.trades_count,
            initial_balance=domain_backtest.initial_balance,
            final_balance=domain_backtest.final_balance,
            created_at=domain_backtest.created_at,
        )
