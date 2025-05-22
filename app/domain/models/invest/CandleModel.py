from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CandleModel:
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime