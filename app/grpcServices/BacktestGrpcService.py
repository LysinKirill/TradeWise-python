import grpc

from app.debug.ExceptionHandler import exception_handler
from app.domain.models.backtest.BacktestStatusModel import BacktestStatusModel
from app.domain.models.backtest.requests.EnqueueBacktestRequestModel import EnqueueBacktestRequestModel
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


    @staticmethod
    def _get_grpc_backtest_status(domain_backtest_status: BacktestStatusModel):
        match domain_backtest_status:
            case BacktestStatusModel.UNKNOWN: return backtest_pb2.BacktestStatus.BacktestStatus_Unknown
            case BacktestStatusModel.PENDING: return backtest_pb2.BacktestStatus.BacktestStatus_Pending
            case BacktestStatusModel.FAILED: return backtest_pb2.BacktestStatus.BacktestStatus_Failed
            case BacktestStatusModel.RUNNING: return backtest_pb2.BacktestStatus.BacktestStatus_Running
            case BacktestStatusModel.COMPLETED: return backtest_pb2.BacktestStatus.BacktestStatus_Completed

        return backtest_pb2.BacktestStatus.BacktestStatus_Unknown


