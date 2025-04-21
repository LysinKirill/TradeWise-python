from dataclasses import dataclass
from app.domain.models.invest import InstrumentStatType
from datetime import datetime


@dataclass(frozen=True)
class GetInstrumentStatRequestModel:
    instrument_id: str
    stat_type: InstrumentStatType.InstrumentStatType
    from_: datetime | None = None
    to: datetime | None = None