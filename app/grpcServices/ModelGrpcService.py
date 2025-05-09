from app.debug.ExceptionLogger import exception_logging
from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.services.IClaimValuesService import IClaimValuesService
from app.domain.services.IModelService import IModelService
from app.infrastructure.JwtAuthorizationDecorator import jwt_authorization
from app.infrastructure.RequestResponseLogging import request_response_logging
from app.proto import model_pb2, model_pb2_grpc


class ModelGrpcService(model_pb2_grpc.ModelServiceServicer):
    def __init__(
            self,
            model_service: IModelService,
            claim_values_service: IClaimValuesService
    ):
        self.model_service = model_service
        self.claim_values_service = claim_values_service

    @exception_logging
    @request_response_logging()
    @jwt_authorization
    async def GetAllModels(self, request, context):
        response = await self.model_service.get_all_models_info()
        return model_pb2.GetAllModelsResponse(
            models=list(map(ModelGrpcService._get_ml_model_info_from_model, response.models))
        )


    @staticmethod
    def _get_ml_model_info_from_model(model_info: ShortModelInfoModel):
        return model_pb2.ShortModelInfo(
            id=model_info.id,
            instrument_id=model_info.instrument_id,
            name=model_info.name,
            type=model_info.model_type,
            created_at=model_info.created_at,
        )