from dataclasses import dataclass
from app.domain.models.invest.InstrumentModel import InstrumentModel

@dataclass(frozen=True)
class GetSupportedInstrumentsResponseModel:
    instruments: list[InstrumentModel]