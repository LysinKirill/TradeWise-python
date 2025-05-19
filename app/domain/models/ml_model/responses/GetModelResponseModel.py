from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GetModelResponseModel:
    id: int
    instrument_id: str
    name: str
    model_type: str
    created_at: datetime