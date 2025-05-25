import asyncio
import logging
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel
from app.domain.services.IModelExecutionService import IModelExecutionService

logger = logging.getLogger(__name__)


class ModelExecutionWorker:
    def __init__(
            self,
            execution_service: IModelExecutionService,
            interval_seconds: int=60
    ):
        self.execution_service = execution_service
        self.interval = interval_seconds
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("Starting Model Execution Worker")
        while self.is_running:
            try:
                await self._run_iteration()
            except Exception as e:
                logger.error(f"Error in worker iteration: {str(e)}")

            await asyncio.sleep(self.interval)

    async def stop(self):
        self.is_running = False
        logger.info("Stopping Model Execution Worker")

    async def _run_iteration(self):
        logger.debug("Running worker iteration")
        pending = (await self.execution_service.get_executions(ExecutionStatusModel.PENDING)).executions

        for execution in pending:
            logger.info(f"Starting execution {execution.id}")
            await self.execution_service.start_execution(execution.id)

        running = (await self.execution_service.get_executions(ExecutionStatusModel.RUNNING)).executions

        for execution in running:
            await self.execution_service.run_execution(execution.id)