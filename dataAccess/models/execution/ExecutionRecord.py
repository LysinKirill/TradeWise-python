from dataclasses import dataclass
from datetime import datetime
from dataAccess.models.execution.ExecutionStatus import ExecutionStatus


@dataclass(frozen=True)
class ExecutionRecord:
    id: int
    user_id: int
    model_id: int
    status: ExecutionStatus
    started_at: datetime | None
    finished_at: datetime | None
    deadline: datetime | None
