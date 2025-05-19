import torch
from abc import ABC, abstractmethod
from typing import Any

from dataAccess.models.model.GetAllModelsInfo import GetAllModelsInfo
from dataAccess.models.model.GetModelResponse import GetModelResponse


class IModelRepository(ABC):
    @abstractmethod
    async def add_model(
            self,
            instrument_id: str,
            name: str,
            model_type: str,
            model: torch.nn.Module,
            configuration: Any | None
        ) -> int:
        pass

    @abstractmethod
    async def get_model(
            self,
            model_id: int,
            model_for_init: torch.nn.Module | None
    ) -> GetModelResponse | None:
        pass

    @abstractmethod
    async def get_all_models_info(self) -> GetAllModelsInfo:
        pass