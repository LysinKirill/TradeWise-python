from dataclasses import dataclass

from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel


@dataclass(frozen=True)
class GetAllModelsInfoResponseModel:
    models: list[ShortModelInfoModel]