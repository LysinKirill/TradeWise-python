# app/services/ModelExecutionService.py
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging

from app.domain.models.execution.ExecutionModel import ExecutionModel
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel
from app.domain.models.execution.requests.StartExecutionRequestModel import StartExecutionRequestModel
from app.domain.models.execution.responses.GetExecutionsResponse import GetExecutionsResponseModel
from app.domain.services.IModelExecutionService import IModelExecutionService
from dataAccess.interfaces.IExecutionRepository import IExecutionRepository
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.models.execution.ExecutionRecord import ExecutionRecord
from dataAccess.models.execution.ExecutionStatus import ExecutionStatus

logger = logging.getLogger(__name__)


class ModelExecutionService(IModelExecutionService):
    def __init__(
            self,
            model_repository: IModelRepository,
            execution_repository: IExecutionRepository
    ):
        self.model_repository = model_repository
        self.execution_repository = execution_repository
        self.active_executions: Dict[int, asyncio.Task] = {}

    async def get_executions(self, status: ExecutionStatusModel | None) -> GetExecutionsResponseModel:
        domain_statuses = [status] if status else list(ExecutionStatusModel)
        statuses_to_fetch = list(map(ModelExecutionService._get_db_status, domain_statuses))

        executions = await self.execution_repository.get_executions_by_status(statuses_to_fetch)


    async def start_execution(self, request: StartExecutionRequestModel) -> int:
        execution = await self.execution_repository.create_execution(
            user_id=request.user_id,
            model_id=request.model_id,
            deadline=request.deadline
        )
        return execution.id


    async def run_execution(self, execution_id: int):
        execution = await self.execution_repository.get_execution(execution_id)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return

        model = await self.model_repository.get_model(execution.model_id)
        if not model:
            logger.error(f"Model with Id = {execution.model_id} not found")
            await self.execution_repository.update_execution_status(
                execution_id,
                ExecutionStatus.FAILED,
                {'error': 'Model not found'}
            )
            return

        # Mark as running
        await self.execution_repository.update_execution_status(
            execution_id, 'running',
            {'started_at': datetime.now(timezone.utc)}
        )

        # Start async task
        task = asyncio.create_task(self._run_model_execution(execution_id, model))
        self.active_executions[execution_id] = task
        task.add_done_callback(lambda t: self._execution_done(execution_id, t))

    async def _run_model_execution(self, execution_id: int, model: Dict):
        try:
            # Load your ML model and execute steps
            # This is a placeholder for your actual model execution logic
            execution = await self.execution_repository.get_execution(execution_id)

            while execution['current_step'] < execution['total_steps']:
                # Execute one step of the model
                result = await self._execute_model_step(model, execution)

                # Update execution progress
                await self.execution_repository.update_execution_progress(
                    execution_id,
                    execution['current_step'] + 1,
                    {'last_result': result}
                )

                execution = await self.execution_repository.get_execution(execution_id)

            # Mark as completed
            await self.execution_repository.update_execution_status(
                execution_id, 'completed',
                {'finished_at': datetime.now(timezone.utc)}
            )

        except Exception as e:
            logger.error(f"Error executing model {execution_id}: {str(e)}")
            await self.execution_repository.update_execution_status(
                execution_id, 'failed',
                {'error': str(e), 'finished_at': datetime.now(timezone.utc)}
            )

    def _execution_done(self, execution_id: int, task: asyncio.Task):
        self.active_executions.pop(execution_id, None)
        if task.exception():
            logger.error(f"Execution {execution_id} failed: {task.exception()}")

    async def _execute_model_step(self, model: Dict, execution: Dict):
        # Implement your actual model step execution here
        # This might involve:
        # 1. Fetching market data
        # 2. Running model prediction
        # 3. Making buy/sell decisions
        # 4. Returning results

        # Placeholder implementation
        await asyncio.sleep(1)  # Simulate work
        return {"step_result": f"Step {execution['current_step']} completed"}

    @staticmethod
    def _get_db_status(status: ExecutionStatusModel) -> ExecutionStatus:
        match status:
            case ExecutionStatusModel.PENDING: return ExecutionStatus.PENDING
            case ExecutionStatusModel.FAILED: return ExecutionStatus.FAILED
            case ExecutionStatusModel.RUNNING: return ExecutionStatus.RUNNING
            case ExecutionStatusModel.COMPLETED: return ExecutionStatus.COMPLETED
        raise ValueError(f"Unknown domain execution status: {status}")

    @staticmethod
    def _get_domain_status(status: ExecutionStatus) -> ExecutionStatusModel:
        match status:
            case ExecutionStatus.PENDING: return ExecutionStatusModel.PENDING
            case ExecutionStatus.FAILED: return ExecutionStatusModel.FAILED
            case ExecutionStatus.RUNNING: return ExecutionStatusModel.RUNNING
            case ExecutionStatus.COMPLETED: return ExecutionStatusModel.COMPLETED
        raise ValueError(f"Unknown DB execution status: {status}")

    @staticmethod
    def _get_domain_execution(db_execution: ExecutionRecord) -> ExecutionModel:
        return ExecutionModel(
            id=db_execution.id,
            user_id=db_execution.user_id,
            model_id=db_execution.model_id,
            status=ModelExecutionService._get_domain_status(db_execution.status),
            started_at=db_execution.started_at,
            finished_at=db_execution.finished_at,
            deadline=db_execution.deadline,
        )