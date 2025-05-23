from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.models.ml_model.responses.GetAllModelsInfoResponseModel import GetAllModelsInfoResponseModel
from app.domain.models.ml_model.responses.GetModelResponseModel import GetModelResponseModel
from app.domain.services.IModelService import IModelService
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.models.model.GetModelResponse import GetModelResponse
from dataAccess.models.model.ShortModelInfo import ShortModelInfo


class ModelService(IModelService):
    def __init__(
        self,
        model_repository: IModelRepository
    ):
        self.model_repository = model_repository


    async def get_model(self, model_id: int) -> GetModelResponseModel:
        model = await self.model_repository.get_model(model_id)
        return GetModelResponseModel(
            id=model.id,
            instrument_id=model.instrument_id,
            name=model.name,
            model_type=model.model_type,
            created_at=model.created_at,
        )


    async def get_all_models_info(self) -> GetAllModelsInfoResponseModel:
        response = await self.model_repository.get_all_models_info()
        return GetAllModelsInfoResponseModel(models=list(map(ModelService._get_domain_model, response.models)))


    @staticmethod
    def _get_domain_model(model: ShortModelInfo):
        return ShortModelInfoModel(
            id=model.id,
            instrument_id=model.instrument_id,
            name=model.name,
            model_type=model.model_type,
            created_at=model.created_at,
        )