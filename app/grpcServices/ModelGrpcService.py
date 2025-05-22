import grpc
from app.debug.ExceptionHandler import exception_handler
from app.domain.exceptions.validation.ValidationErrorCode import ValidationErrorCode
from app.domain.exceptions.validation.ValidationException import ValidationException
from app.domain.models.execution.ExecutionModel import ExecutionModel
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel
from app.domain.models.execution.requests.CreateExecutionRequestModel import CreateExecutionRequestModel
from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.models.user.UserInfoModel import UserInfoModel
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

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def StartExecution(self, request, context):
        if request.max_execution_duration_seconds <= 0:
            raise ValidationException(ValidationErrorCode.ExpectedPositiveValue, "max execution duration must be positive")
        if request.initial_balance <= 0:
            raise ValidationException(ValidationErrorCode.ExpectedPositiveValue, "allocated balance must be positive")

        user_email = await self.claim_values_service.get_email()
        started_execution_id = await self.model_execution_service.create_execution(
            CreateExecutionRequestModel(
                user_email=user_email,
                model_id=request.model_id,
                allocated_balance=request.initial_balance,
                max_duration_in_seconds=request.max_execution_duration_seconds
            )
        )
        return model_pb2.StartExecutionResponse(execution_id=started_execution_id)

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetExecutionStatus(self, request, context):
        response = await self.model_execution_service.get_execution_status(request.execution_id)
        return model_pb2.GetExecutionStatusResponse(status=ModelGrpcService._get_grpc_execution_status(response))

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def GetExecutionInfo(self, request, context):
        response = await self.model_execution_service.get_execution(request.execution_id)
        return ModelGrpcService._get_grpc_execution(response)

    @exception_handler
    @request_response_logging()
    @jwt_authorization
    async def StopExecution(self, request, context):
        await self.model_execution_service.stop_execution(request.execution_id)
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

    @staticmethod
    def _get_grpc_execution_status(domain_execution_status: ExecutionStatusModel):
        match domain_execution_status:
            case ExecutionStatusModel.UNKNOWN: return model_pb2.ExecutionStatus.ExecutionStatus_Unknown
            case ExecutionStatusModel.PENDING: return model_pb2.ExecutionStatus.ExecutionStatus_Pending
            case ExecutionStatusModel.FAILED: return model_pb2.ExecutionStatus.ExecutionStatus_Failed
            case ExecutionStatusModel.RUNNING: return model_pb2.ExecutionStatus.ExecutionStatus_Running
            case ExecutionStatusModel.COMPLETED: return model_pb2.ExecutionStatus.ExecutionStatus_Completed

        return model_pb2.ExecutionStatus.ExecutionStatus_Unknown

    @staticmethod
    def _get_grpc_execution(domain_execution: ExecutionModel):
        return model_pb2.ExecutionInfo(
            execution_id=domain_execution.id,
            status=ModelGrpcService._get_grpc_execution_status(domain_execution.status),
            started_at=domain_execution.started_at,
            finished_at=domain_execution.finished_at,
            deadline=domain_execution.deadline,
            max_budget=domain_execution.max_budget,
            current_spent=domain_execution.current_spent,
            shares_owned=domain_execution.shares_owned,
            user_info=ModelGrpcService._get_grpc_user_info(domain_execution.user_info),
            model_info=ModelGrpcService._get_ml_model_info_from_model(domain_execution.model_info),
        )


    @staticmethod
    def _get_grpc_user_info(user_info: UserInfoModel):
        return model_pb2.UserInfo(
            id=user_info.id,
            email=user_info.email,
        )