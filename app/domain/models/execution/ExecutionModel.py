from dataclasses import dataclass
from datetime import datetime
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel


@dataclass(frozen=True)
class ExecutionModel:
    id: int
    user_id: int
    model_id: int
    status: ExecutionStatusModel
    started_at: datetime | None
    finished_at: datetime | None
    deadline: datetime | None
