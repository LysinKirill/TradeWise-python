import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, AsyncGenerator
import logging
import numpy as np
import torch

from app.domain.exceptions.execution.ExecutionNotFoundException import ExecutionNotFoundException
from app.domain.exceptions.execution.InvalidStateTransitionException import InvalidStateTransitionException
from app.domain.exceptions.model.ModelNotFoundException import ModelNotFoundException
from app.domain.models.execution.ExecutionModel import ExecutionModel
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel
from app.domain.models.execution.requests.CreateExecutionRequestModel import CreateExecutionRequestModel
from app.domain.models.execution.responses.GetExecutionsResponse import GetExecutionsResponseModel
from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.models.user.UserInfoModel import UserInfoModel
from app.domain.models.invest.CandleModel import CandleModel
from app.domain.services.IModelExecutionService import IModelExecutionService
from app.domain.services.IUserService import IUserService
from dataAccess.interfaces.IExecutionRepository import IExecutionRepository
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.models.common.ModelInfo import ModelInfo
from dataAccess.models.common.UserInfo import UserInfo
from dataAccess.models.execution.ExecutionRecord import ExecutionRecord
from dataAccess.models.execution.ExecutionStatus import ExecutionStatus
from dataAccess.models.model.GetModelResponse import GetModelResponse
from ml.data.interface.IBroker import IBroker
from ml.data.interface.ICandleGenerator import ICandleGenerator
from ml.data.interface.ITradingWindowManager import ITradingWindowManager
from ml.data.model.OperationType import OperationType
from ml.dataAugmentation.Normalizer import Normalizer

logger = logging.getLogger(__name__)


class ModelExecutionService(IModelExecutionService):
    DEFAULT_BUY_SIGNAL = 0.0008
    DEFAULT_SELL_SIGNAL = 0.0009
    REFRESH_INTERVAL_SECONDS = 60

    def __init__(
            self,
            model_repository: IModelRepository,
            execution_repository: IExecutionRepository,
            user_service: IUserService,
            candle_generator_factory: ICandleGenerator,
            broker: IBroker,
            trading_window_manager: ITradingWindowManager,
            device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.user_service = user_service
        self.model_repository = model_repository
        self.execution_repository = execution_repository
        self.candle_generator_factory = candle_generator_factory
        self.broker = broker
        self.trading_window_manager = trading_window_manager
        self.device = device

        self.active_executions: Dict[int, asyncio.Task] = {}
        self.candle_data: Dict[str, tuple[datetime, list]] = {}
        self.candle_generators: Dict[str, AsyncGenerator[CandleModel | None, None]] = {}
        self.lock = asyncio.Lock()

    async def get_execution(self, execution_id: int) -> ExecutionModel:
        execution = await self.execution_repository.get_execution(execution_id)
        if execution is None:
            raise ExecutionNotFoundException(execution_id, "PostgreSQL model_executions table")

        return ModelExecutionService._get_domain_execution(execution)

    async def get_execution_status(self, execution_id: int) -> ExecutionStatusModel:
        return (await self.get_execution(execution_id)).status

    async def get_executions(self, status: ExecutionStatusModel | None) -> GetExecutionsResponseModel:
        domain_statuses = [status] if status else list(ExecutionStatusModel)
        statuses_to_fetch = list(map(ModelExecutionService._get_db_status, domain_statuses))

        executions = await self.execution_repository.get_executions_by_status(statuses_to_fetch)
        return GetExecutionsResponseModel(executions=list(map(ModelExecutionService._get_domain_execution, executions)))


    async def create_execution(self, request: CreateExecutionRequestModel) -> int:
        deadline = datetime.now(timezone.utc) + timedelta(seconds=request.max_duration_in_seconds)
        # TODO: replace with get_short_model_info
        model = await self.model_repository.get_model(request.model_id)
        if model is None:
            raise ModelNotFoundException(request.model_id, model_source="PostgreSQL model table")

        execution_id = await self.execution_repository.create_execution(
            user_email=request.user_email,
            model_id=request.model_id,
            deadline=deadline,
            allocated_amount=request.allocated_balance
        )

        logger.info(f"Created execution with ID {execution_id}")
        return execution_id

    async def start_execution(self, execution_id: int) -> bool:
        try:
            execution = await self.execution_repository.get_execution(execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return False

            if execution.status != ExecutionStatus.PENDING:
                logger.error(f"Execution {execution_id} is in state {execution.status}. Can only start execution with PENDING status")
                return False

            success = await self.execution_repository.update_execution_status(
                execution_id,
                ExecutionStatus.RUNNING,
                started_at=datetime.now(timezone.utc)
            )
            logger.info(f"Started execution with ID {execution_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to start execution {execution_id}: {e}")
            return False

    async def run_execution(self, execution_id: int) -> bool:
        execution = await self.execution_repository.get_execution(execution_id)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return False

        if datetime.now(timezone.utc) > execution.deadline:
            await self._complete_execution(execution_id)
            return False

        model_response = await self.model_repository.get_model(execution.model_info.id, None)
        if not model_response:
            logger.error(f"Model {execution.model_info.id} not found")
            await self._mark_execution_failed(execution_id)
            return False

        instrument_id = model_response.instrument_id
        lookback = model_response.config.get('lookback_window', 16) if model_response.config else 16

        try:
            async with (self.lock):
                if instrument_id not in self.candle_generators:
                    gen = self.candle_generator_factory.generate_candles(
                        instrument_id,
                        preload_candles_count=lookback
                    )
                    self.candle_generators[instrument_id] = gen

                    initial_candles = []
                    async for candle in gen:
                        initial_candles.append(candle)
                        if len(initial_candles) >= lookback:
                            break

                    self.candle_data[instrument_id] = (datetime.now(timezone.utc), initial_candles)

                if (
                        len(self.candle_data[instrument_id][1]) == 0 or
                        (datetime.now(timezone.utc) - self.candle_data[instrument_id][0]).seconds >= ModelExecutionService.REFRESH_INTERVAL_SECONDS
                ):
                    candle = await anext(self.candle_generators[instrument_id])
                    if not candle:
                        logger.warning(f"No new candle for {instrument_id}")
                        return True

                    current_history = self.candle_data[instrument_id][1]
                    current_history.append(candle)
                    if len(current_history) >= lookback:
                        current_history = current_history[-lookback:]
                    self.candle_data[instrument_id] = (datetime.now(timezone.utc), current_history)


            if len(self.candle_data[instrument_id][1]) >= lookback:
                await self._process_single_step(
                    execution_id,
                    instrument_id,
                    model_response,
                    lookback
                )

            return True

        except Exception as e:
            logger.error(f"Error in execution {execution_id}: {str(e)}")
            await self._mark_execution_failed(execution_id)
            return False


    async def stop_execution(self, execution_id: int):
        execution = await self.execution_repository.get_execution(execution_id)
        if not execution:
            raise ExecutionNotFoundException(execution_id, "PostgreSQL model_executions table")

        if execution.status == ExecutionStatus.FAILED:
            logger.error(f"Attempted to stop execution in failed status. Execution Id: {execution_id}")
            raise InvalidStateTransitionException(
                ModelExecutionService._get_domain_status(execution.status),
                ModelExecutionService._get_domain_status(ExecutionStatus.COMPLETED)
            )

        success = await self.execution_repository.update_execution_status(
            execution_id,
            ExecutionStatus.COMPLETED,
            finished_at=datetime.now(timezone.utc)
        )
        if success:
            logger.info(f"Stopped execution with ID {execution_id}")



    async def _process_single_step(
            self,
            execution_id: int,
            instrument_id: str,
            model_info: GetModelResponse,
            lookback: int
    ):
        model = model_info.model.to(self.device)
        model.eval()
        normalizer = self._create_normalizer(model_info.config)
        trading_params = model_info.config.get('trading_params', {}) if model_info.config else {}

        candles = self.candle_data[instrument_id][1][-lookback:]
        current_candle = candles[-1]

        features = np.array([[c.close] for c in candles])
        normalized_data = normalizer.transform(features)
        seq = torch.FloatTensor(normalized_data).unsqueeze(0).to(self.device)

        with torch.no_grad():
            pred = model(seq).cpu().numpy()[0]
            pred_price = normalizer.inverse_transform(
                np.array([[pred, pred, pred, pred, 0]])
            )[0][3]

        current_price = current_candle.close
        expected_return = (pred_price - current_price) / current_price


        trade_available = await self.trading_window_manager.check_trade_available(
            instrument_id=instrument_id,
            timestamp=current_candle.timestamp,
        )

        if not trade_available:
            return

        execution = await self.execution_repository.get_execution(execution_id)
        if not execution:
            return

        if (expected_return > trading_params.get('buy_signal', ModelExecutionService.DEFAULT_BUY_SIGNAL)
                and execution.shares_owned == 0):
            await self._execute_buy(
                execution,
                current_price,
            )
        elif (expected_return < -trading_params.get('sell_signal', ModelExecutionService.DEFAULT_SELL_SIGNAL)
              and execution.shares_owned > 0):
            await self._execute_sell(
                execution,
                current_price
            )

    def _execution_done(self, execution_id: int, task: asyncio.Task):
        self.active_executions.pop(execution_id, None)
        if task.exception():
            logger.error(f"Execution {execution_id} failed: {task.exception()}")

    async def _execute_buy(
            self,
            execution: ExecutionRecord,
            price: float
    ):
        user = execution.user_info
        model = execution.model_info

        max_lots = await self.broker.get_max_lots(
            invest_api_key=user.invest_api_key,
            account_id=user.invest_account_id,
            instrument_id=model.instrument_id,
            operation=OperationType.Buy,
            expected_price=price
        )

        if max_lots > 0:
            success = await self.broker.place_order(
                invest_api_key=user.invest_api_key,
                account_id=user.invest_account_id,
                instrument_id=model.instrument_id,
                operation=OperationType.Buy,
                quantity=max_lots,
                expected_price=price,
            )

            if success:
                cost = max_lots * price
                await self.execution_repository.update_execution_financials(
                    execution.id,
                    current_spent_increment=cost,
                    shares_owned_increment=max_lots
                )

    async def _execute_sell(
            self,
            execution: ExecutionRecord,
            price: float,
    ):
        user = execution.user_info
        model = execution.model_info

        max_lots = min(
            await self.broker.get_max_lots(
                invest_api_key=user.invest_api_key,
                instrument_id=model.instrument_id,
                account_id=user.invest_account_id,
                operation=OperationType.Sell,
                expected_price=price),
            execution.shares_owned
        )

        if max_lots > 0:
            success = await self.broker.place_order(
                invest_api_key=user.invest_api_key,
                account_id=user.invest_account_id,
                instrument_id=model.instrument_id,
                operation=OperationType.Sell,
                quantity=max_lots,
                expected_price=price,
            )

            if success:
                revenue = max_lots * price
                await self.execution_repository.update_execution_financials(
                    execution.id,
                    current_spent_increment=-revenue,
                    shares_owned_increment=-max_lots
                )

    @staticmethod
    def _create_normalizer(config: dict) -> Normalizer:
        if config and 'normalizer_mins' in config and 'normalizer_maxs' in config:
            return Normalizer(
                mins=np.array(config['normalizer_mins']),
                maxs=np.array(config['normalizer_maxs'])
            )
        return Normalizer()


    async def _mark_execution_failed(self, execution_id: int):
        await self.execution_repository.update_execution_status(
            execution_id,
            ExecutionStatus.FAILED,
            finished_at=datetime.now(timezone.utc)
        )

    async def _complete_execution(self, execution_id: int):
        await self.execution_repository.update_execution_status(
            execution_id,
            ExecutionStatus.COMPLETED,
            finished_at=datetime.now(timezone.utc)
        )

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
            user_info=ModelExecutionService._get_domain_user(db_execution.user_info),
            model_info=ModelExecutionService._get_domain_model(db_execution.model_info),
            status=ModelExecutionService._get_domain_status(db_execution.status),
            started_at=db_execution.started_at,
            finished_at=db_execution.finished_at,
            deadline=db_execution.deadline,
            max_budget=db_execution.max_budget,
            current_spent=db_execution.current_spent,
            shares_owned=db_execution.shares_owned,
        )

    @staticmethod
    def _get_domain_user(db_user: UserInfo) -> UserInfoModel:
        return UserInfoModel(
            id=db_user.id,
            email=db_user.email,
            invest_api_key=db_user.invest_api_key,
            invest_account_id=db_user.invest_account_id,
        )

    @staticmethod
    def _get_domain_model(db_model: ModelInfo) -> ShortModelInfoModel:
        return ShortModelInfoModel(
            id=db_model.id,
            instrument_id=db_model.instrument_id,
            name=db_model.name,
            model_type=db_model.type,
            created_at=db_model.created_at,
        )

    @staticmethod
    def _get_domain_status(db_status: ExecutionStatus) -> ExecutionStatusModel:
        match db_status:
            case ExecutionStatus.PENDING: return ExecutionStatusModel.PENDING
            case ExecutionStatus.FAILED: return ExecutionStatusModel.FAILED
            case ExecutionStatus.RUNNING: return ExecutionStatusModel.RUNNING
            case ExecutionStatus.COMPLETED: return ExecutionStatusModel.COMPLETED
        return ExecutionStatusModel.UNKNOWN