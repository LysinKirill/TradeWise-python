from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GetCandlesRequestModel:
    instrument_id: str
    from_: datetime | None = None
    to: datetime | None = None