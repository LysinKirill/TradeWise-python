import grpc
from app.debug.ExceptionLogger import exception_handler
from app.domain.models.execution.requests.StartExecutionRequestModel import StartExecutionRequestModel
from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.services.IClaimValuesService import IClaimValuesService
from app.domain.services.IModelExecutionService import IModelExecutionService
from app.domain.services.IModelService import IModelService
from app.infrastructure.JwtAuthorizationDecorator import jwt_authorization
from app.infrastructure.RequestResponseLogging import request_response_logging
from app.proto import model_pb2, model_pb2_grpc
from google.protobuf import empty_pb2


class ModelGrpcService(model_pb2_grpc.ModelServiceServicer):
    def __init__(
            self,
            model_service: IModelService,
            model_execution_service: IModelExecutionService,
            claim_values_service: IClaimValuesService
    ):
        self.model_service = model_service
        self.model_execution_service = model_execution_service
        self.claim_values_service = claim_values_service

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetAllModels(self, request, context):
        response = await self.model_service.get_all_models_info()
        return model_pb2.GetAllModelsResponse(
            models=list(map(ModelGrpcService._get_ml_model_info_from_model, response.models))
        )

    async def StartExecution(self, request, context):
        user_email = await self.claim_values_service.get_email()
        started_execution_id = await self.model_execution_service.start_execution(
            StartExecutionRequestModel(
                user_email=user_email,
                model_id=request.model_id,
                allocated_balance=request.initial_balance,
                max_duration_in_seconds=request.max_execution_duration_seconds
            )
        )
        return model_pb2.StartExecutionResponse(execution_id=started_execution_id)

    async def GetExecutionStatus(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "Method is not yet implemented")
        return model_pb2.GetExecutionStatusResponse(status=model_pb2.ExecutionStatus.ExecutionStatus_Running)

    async def StopExecution(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "Method is not yet implemented")
        return empty_pb2.Empty()


    @staticmethod
    def _get_ml_model_info_from_model(model_info: ShortModelInfoModel):
        return model_pb2.ShortModelInfo(
            id=model_info.id,
            instrument_id=model_info.instrument_id,
            name=model_info.name,
            type=model_info.model_type,
            created_at=model_info.created_at,
        )