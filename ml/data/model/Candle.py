from dataclasses import dataclass
from datetime import datetime


@dataclass
class Candle:
    close: float
    timestamp: datetime