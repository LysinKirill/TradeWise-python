from abc import ABC, abstractmethod

from app.domain.models.ml_model.responses.GetAllModelsInfoResponseModel import GetAllModelsInfoResponseModel


class IModelService(ABC):
    @abstractmethod
    async def get_all_models_info(self) -> GetAllModelsInfoResponseModel:
        pass