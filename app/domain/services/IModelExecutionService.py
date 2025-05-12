from abc import ABC, abstractmethod
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel
from app.domain.models.execution.requests.StartExecutionRequestModel import StartExecutionRequestModel
from app.domain.models.execution.responses.GetExecutionsResponse import GetExecutionsResponseModel


class IModelExecutionService(ABC):
    @abstractmethod
    async def get_executions(self, status: ExecutionStatusModel | None) -> GetExecutionsResponseModel:
        pass

    @abstractmethod
    async def start_execution(self, request: StartExecutionRequestModel) -> int:
        pass

    @abstractmethod
    async def run_execution(self, execution_id: int):
        pass