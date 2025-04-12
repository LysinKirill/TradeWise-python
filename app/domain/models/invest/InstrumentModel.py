from dataclasses import dataclass

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