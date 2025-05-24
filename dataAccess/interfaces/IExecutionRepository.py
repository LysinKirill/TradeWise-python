from abc import ABC, abstractmethod
from datetime import datetime
from dataAccess.models.execution.ExecutionRecord import ExecutionRecord
from dataAccess.models.execution.ExecutionStatus import ExecutionStatus


class IExecutionRepository(ABC):
    @abstractmethod
    async def create_execution(
        self,
        user_id: int,
        model_id: int,
        allocated_amount: float,
        deadline: datetime | None = None,
    ) -> int:
        pass

    @abstractmethod
    async def get_execution(self, execution_id: int) -> ExecutionRecord | None:
        pass

    @abstractmethod
    async def get_executions_by_status(
        self,
        statuses: list[ExecutionStatus]
    ) -> list[ExecutionRecord]:
        pass

    @abstractmethod
    async def update_execution_status(
        self,
        execution_id: int,
        status: ExecutionStatus,
        started_at: datetime | None = None,
        finished_at:datetime | None = None
    ) -> bool:
        pass

    @abstractmethod
    async def set_execution_deadline(
        self,
        execution_id: int,
        deadline: datetime
    ) -> bool:
        pass

    @abstractmethod
    async def cleanup_expired_executions(self) -> int:
        pass

    async def update_execution_financials(
            self,
            execution_id: int,
            current_spent_increment: float,
            shares_owned_increment: int
    ) -> bool:
        pass