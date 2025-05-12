from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StartExecutionRequestModel:
    user_id: int
    model_id: int
    deadline: datetime | None
