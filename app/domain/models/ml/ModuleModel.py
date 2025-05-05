from torch import nn
from datetime import datetime
from dataclasses import dataclass
from ml.dataAugmentation.Normalizer import Normalizer


@dataclass(frozen=True)
class ModuleModel:
    id: str
    instrument_id: str
    name: str
    created_at: datetime
    model: nn.Module
    normalizer: Normalizer