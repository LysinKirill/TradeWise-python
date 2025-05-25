import grpc

from app.domain.models.backtest.requests.EnqueueBacktestRequestModel import EnqueueBacktestRequestModel
from app.domain.services.IBacktestService import IBacktestService
from app.domain.services.IClaimValuesService import IClaimValuesService
from app.proto import backtest_pb2, backtest_pb2_grpc


class BacktestGrpcService(backtest_pb2_grpc.BacktestServiceServicer):
    def __init__(
        self,
        claim_values_service: IClaimValuesService,
        backtest_service: IBacktestService
    ):
        self.claim_values_service = claim_values_service
        self.backtest_service = backtest_service


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

    async def GetBacktestStatus(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "Method is not yet implemented")
        return backtest_pb2.GetBacktestStatusResponse(status=backtest_pb2.BacktestStatus.BacktestStatus_Running)
