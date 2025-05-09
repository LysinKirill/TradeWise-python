from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FullModelInfo:
    id: int | None
    instrument_id: str
    name: str
    model_type: str
    created_at: datetime
    model_configuration: dataclass
    normalizer_mins: list[float]
    normalizer_maxs: list[float]
