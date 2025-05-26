import asyncio
import logging

from app.domain.models.backtest.BacktestStatusModel import BacktestStatusModel
from app.domain.services.IBacktestService import IBacktestService

logger = logging.getLogger(__name__)


class BacktestExecutionWorker:
    def __init__(
            self,
            backtest_service: IBacktestService,
            interval_seconds: int=60
    ):
        self.backtest_service = backtest_service
        self.interval = interval_seconds
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("Starting Backtest Execution Worker")
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
        running = await self.backtest_service.get_first_backtest_by_status(BacktestStatusModel.RUNNING)
        if running:
            logger.warning(f"Found backtest in Running status. Backtest Id: {running.id}. Attempting to continue run")
            backtest_to_run = running
        else:
            backtest_to_run = await self.backtest_service.get_first_backtest_by_status(BacktestStatusModel.PENDING)


        if backtest_to_run is None:
            logger.debug("No backtest queued to run. Skipping iteration")
            return

        try:
            await self.backtest_service.run_backtest(backtest_to_run.id)
        except Exception as e:
            logger.error(f"Error running backtest with id: {backtest_to_run.id}: {str(e)}")
            await self.backtest_service.update_backtest_status(backtest_to_run.id, BacktestStatusModel.FAILED)
            raise
