from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EnqueueBacktestRequestModel:
    user_email: str
    model_id: int
    from_: datetime
    to: datetime
    initial_balance: float
