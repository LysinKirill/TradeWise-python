from dataclasses import dataclass
from app.domain.models.execution.ExecutionModel import ExecutionModel


@dataclass(frozen=True)
class GetExecutionsResponseModel:
    executions: list[ExecutionModel]
