from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.models.ml_model.responses.GetAllModelsInfoResponseModel import GetAllModelsInfoResponseModel
from app.domain.services.IModelService import IModelService
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.models.model.ShortModelInfo import ShortModelInfo


class ModelService(IModelService):
    def __init__(
        self,
        model_repository: IModelRepository,
        fallback_model_repository: IModelRepository,
    ):
        self.model_repository = model_repository
        self.fallback_model_repository = fallback_model_repository


    async def get_all_models_info(self) -> GetAllModelsInfoResponseModel:
        repository_response = await self.model_repository.get_all_models_info()
        model_names_pg = {x.name for x in repository_response.models}
        models = repository_response.models

        fallback_model_repository_response = await self.fallback_model_repository.get_all_models_info()
        for fallback_model in fallback_model_repository_response.models:
            if fallback_model.name not in model_names_pg:
                models.append(fallback_model)

        return GetAllModelsInfoResponseModel(models=list(map(ModelService._get_domain_model, models)))


    @staticmethod
    def _get_domain_model(model: ShortModelInfo):
        return ShortModelInfoModel(
            id=model.id,
            instrument_id=model.instrument_id,
            name=model.name,
            model_type=model.model_type,
            created_at=model.created_at,
        )