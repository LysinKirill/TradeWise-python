from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class LstmTrainingConfiguration:
    instrument_id: str
    sequence_length: int
    train_period_start_utc: datetime
    train_period_end_utc: datetime
    batch_size: int
    epochs: int

