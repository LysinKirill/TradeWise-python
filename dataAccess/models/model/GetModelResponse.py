from datetime import datetime
from torch.nn import Module
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GetModelResponse:
    id: int
    instrument_id: str
    name: str
    model_type: str
    model: Module
    config: Any | None
    created_at: datetime
