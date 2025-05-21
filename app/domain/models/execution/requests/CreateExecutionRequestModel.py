from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateExecutionRequestModel:
    user_email: str
    model_id: int
    allocated_balance: float
    max_duration_in_seconds: int
