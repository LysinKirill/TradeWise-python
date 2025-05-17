import grpc
from app.proto import backtest_pb2, backtest_pb2_grpc


class BacktestGrpcService(backtest_pb2_grpc.BacktestServiceServicer):

    async def StartBacktest(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "Method is not yet implemented")
        return backtest_pb2.StartBacktestResponse(backtest_id=102)

    async def GetBacktestStatus(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "Method is not yet implemented")
        return backtest_pb2.GetBacktestStatusResponse(status=backtest_pb2.BacktestStatus.BacktestStatus_Running)
