from dataclasses import dataclass
from dataAccess.models.model.ShortModelInfo import ShortModelInfo


@dataclass(frozen=True)
class GetAllModelsInfo:
    models: list[ShortModelInfo]