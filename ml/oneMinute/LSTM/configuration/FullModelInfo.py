from dataclasses import dataclass
from datetime import datetime
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration


@dataclass(frozen=True)
class FullModelInfo:
    id: int
    instrument_id: str
    name: str
    model_type: str
    created_at: datetime
    lstm_configuration: LstmConfiguration
    normalizer_mins: list[float]
    normalizer_maxs: list[float]
