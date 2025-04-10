from dataclasses import dataclass
from RiskLevelModel import RiskLevelModel

@dataclass(frozen=True)
class InstrumentModel:
    id: str
    figi: str | None
    name: str
    lot: int
    currency: str
    sector: str
    buy_available: bool
    sell_available: bool
    risk_level: RiskLevelModel