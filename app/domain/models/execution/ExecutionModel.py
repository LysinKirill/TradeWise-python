from dataclasses import dataclass
from datetime import datetime
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel
from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.models.user.UserInfoModel import UserInfoModel


@dataclass(frozen=True)
class ExecutionModel:
    id: int
    status: ExecutionStatusModel
    started_at: datetime | None
    finished_at: datetime | None
    deadline: datetime | None
    max_budget: float
    current_spend: float
    shares_owned: int
    user_info: UserInfoModel
    model_info: ShortModelInfoModel