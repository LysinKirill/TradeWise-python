from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ModelInfo:
    id: int
    instrument_id: str
    name: str
    type: str
    created_at: datetime