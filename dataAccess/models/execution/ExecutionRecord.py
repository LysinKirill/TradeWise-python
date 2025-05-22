from dataclasses import dataclass
from datetime import datetime
from dataAccess.models.common.ModelInfo import ModelInfo
from dataAccess.models.common.UserInfo import UserInfo
from dataAccess.models.execution.ExecutionStatus import ExecutionStatus


@dataclass(frozen=True)
class ExecutionRecord:
    id: int
    status: ExecutionStatus
    started_at: datetime | None
    finished_at: datetime | None
    deadline: datetime | None
    max_budget: float
    current_spent: float
    shares_owned: int
    user_info: UserInfo
    model_info: ModelInfo