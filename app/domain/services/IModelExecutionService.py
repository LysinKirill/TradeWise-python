from abc import ABC, abstractmethod
from app.domain.models.execution.ExecutionModel import ExecutionModel
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel
from app.domain.models.execution.requests.CreateExecutionRequestModel import CreateExecutionRequestModel
from app.domain.models.execution.responses.GetExecutionsResponse import GetExecutionsResponseModel


class IModelExecutionService(ABC):
    @abstractmethod
    async def get_execution(self, execution_id: int) -> ExecutionModel:
        pass

    @abstractmethod
    async def get_executions(self, status: ExecutionStatusModel | None) -> GetExecutionsResponseModel:
        pass

    @abstractmethod
    async def get_execution_status(self, execution_id: int) -> ExecutionStatusModel:
        pass

    @abstractmethod
    async def create_execution(self, request: CreateExecutionRequestModel) -> int:
        pass

    @abstractmethod
    async def start_execution(self, execution_id: int) -> bool:
        pass

    @abstractmethod
    async def run_execution(self, execution_id: int) -> bool:
        pass

    @abstractmethod
    async def stop_execution(self, execution_id: int):
        pass