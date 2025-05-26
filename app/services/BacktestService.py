import numpy as np
from datetime import time, timezone, datetime
from app.domain.exceptions.backtest.BacktestAlreadyQueuedException import BacktestAlreadyQueuedException
from app.domain.exceptions.backtest.BacktestNotFoundException import BacktestNotFoundException
from app.domain.exceptions.backtest.BacktestResult import BacktestResult
from app.domain.exceptions.backtest.InvalidStateTransitionException import InvalidStateTransitionException
from app.domain.exceptions.model.ModelNotFoundException import ModelNotFoundException
from app.domain.exceptions.user.UserNotFoundException import UserNotFoundException
from app.domain.models.backtest.BacktestModel import BacktestModel
from app.domain.models.backtest.BacktestStatusModel import BacktestStatusModel
from app.domain.models.backtest.requests.EnqueueBacktestRequestModel import EnqueueBacktestRequestModel
from app.domain.models.backtest.responses.EnqueueBacktestResponseModel import EnqueueBacktestResponseModel
from app.domain.models.backtest.responses.GetBacktestForUserResponseModel import GetBacktestForUserResponseModel
from app.domain.services.IBacktestService import IBacktestService
from app.domain.services.IClaimValuesService import IClaimValuesService
from app.mappers.domain_dal.CommonMapper import CommonMapper
from app.services.ModelExecutionService import ModelExecutionService
from dataAccess.interfaces.IBacktestRepository import IBacktestRepository
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.interfaces.IUserRepository import IUserRepository
from dataAccess.models.backtest.BacktestRecord import BacktestRecord
from dataAccess.models.backtest.BacktestStatus import BacktestStatus
from externalClients.TInvestApi.handlers.InstrumentsClient import InstrumentsClient
from ml.data.HistoryCandleGenerator import HistoryCandleGenerator
from ml.data.PresetTradingWindowManager import PresetTradingWindowManager
from ml.data.TestBroker import TestBroker
from ml.dataAugmentation.Normalizer import Normalizer
from ml.runner.StockTrader import StockTrader
from ml.runner.configuration.TradingConfiguration import TradingConfiguration


class BacktestService(IBacktestService):
    def __init__(
            self,
            backtest_repository: IBacktestRepository,
            user_repository: IUserRepository,
            model_repository: IModelRepository,
            instruments_client: InstrumentsClient,
            claim_values_service: IClaimValuesService,
    ):
        self.backtest_repository = backtest_repository
        self.user_repository = user_repository
        self.model_repository = model_repository
        self.instruments_client = instruments_client
        self.claim_values_service = claim_values_service


    async def enqueue_backtest(self, request: EnqueueBacktestRequestModel) -> EnqueueBacktestResponseModel:
        user = await self.user_repository.get_user_by_email(request.user_email)
        if user is None:
            raise UserNotFoundException(user_email=request.user_email, source="PostgreSQL user table")

        # TODO: replace with get_short_model_info
        model = await self.model_repository.get_model(request.model_id)
        if model is None:
            raise ModelNotFoundException(request.model_id, model_source="PostgreSQL model table")

        user_backtests = await self.backtest_repository.get_user_backtests(user_id=user.id)
        already_queued_backtest_ids = list(
            map(
                lambda backtest: backtest.id,
                filter(
                    lambda backtest: backtest.status == BacktestStatus.PENDING or
                                     backtest.status == BacktestStatus.RUNNING,
                    user_backtests
                )
            )
        )

        if already_queued_backtest_ids:
            raise BacktestAlreadyQueuedException(user_id=user.id, backtest_ids=already_queued_backtest_ids)

        backtest_id = await self.backtest_repository.create_backtest(
            user_id=user.id,
            model_id=model.id,
            allocated_amount=request.initial_balance,
            from_=request.from_,
            to=request.to,
        )

        return EnqueueBacktestResponseModel(backtest_id=backtest_id)

    async def get_backtest(self, backtest_id: int) -> BacktestModel:
        db_backtest = await self.backtest_repository.get_backtest(backtest_id)
        if db_backtest is None:
            raise BacktestNotFoundException(backtest_id=backtest_id, backtest_source="PostgreSQL backtest table")

        return BacktestService._get_domain_backtest(db_backtest)

    async def get_backtest_status(self, backtest_id: int) -> BacktestStatusModel:
        return (await self.get_backtest(backtest_id)).status

    async def get_first_backtest_by_status(self, status: BacktestStatusModel) -> BacktestModel | None:
        return await self.backtest_repository.get_first_backtest_by_status(
            BacktestService._get_db_backtest_status(status))

    async def run_backtest(self, backtest_id: int) -> None:
        # TODO: add support for specifying commission
        default_commission = 0.0005

        db_backtest = await self.backtest_repository.get_backtest(backtest_id)
        # TODO: raise proper business error
        if db_backtest is None:
            raise Exception("Backtest not found")

        backtest = BacktestService._get_domain_backtest(db_backtest)
        user_info = backtest.user_info

        model = await self.model_repository.get_model(backtest.model_info.id)

        # TODO: raise proper business error
        if model is None:
            raise Exception("Model not found")


        invest_api_key = user_info.invest_api_key
        sell_signal = ModelExecutionService.DEFAULT_SELL_SIGNAL
        buy_signal = ModelExecutionService.DEFAULT_BUY_SIGNAL
        initial_balance = backtest.initial_balance

        client_response_instruments = await self.instruments_client.get_instruments(instrument_ids=[model.instrument_id])

        # TODO: check that client response contains exactly one instrument
        lot_size = client_response_instruments[0].lot

        test_candle_source = HistoryCandleGenerator(
            invest_api_key=invest_api_key,
            start_timestamp=backtest.test_period_start,
            end_timestamp=backtest.test_period_end,
            instrument_id=model.instrument_id
        )

        test_trading_window_manager = PresetTradingWindowManager(
            trading_windows=[(time(hour=7, minute=0, second=0, microsecond=0),
                              time(hour=16, minute=50, second=0, microsecond=0))],
        )

        test_broker = TestBroker(
            start_balance=backtest.initial_balance,
            lot_size=lot_size,
            commission=default_commission,
        )

        test_trading_config = TradingConfiguration(
            sell_signal=sell_signal,
            buy_signal=buy_signal,
        )

        normalizer = self._create_normalizer(model.config)

        test_trader = StockTrader(
            model=model.model,
            trading_configuration=test_trading_config,
            invest_api_key=invest_api_key,
            instrument_id=model.instrument_id,
            candle_source=test_candle_source,
            broker=test_broker,
            trading_window_manager=test_trading_window_manager,
            account_id=user_info.invest_account_id,
            scaler=normalizer
        )


        start_timestamp = datetime.now(timezone.utc)
        await self.backtest_repository.update_backtest_status(backtest_id=backtest_id, status=BacktestStatus.RUNNING)
        await test_trader.start_trading()
        end_timestamp = datetime.now(timezone.utc)
        final_portfolio_value = test_broker.portfolio_value

        backtest_result = BacktestResult(
            backtest_id=backtest_id,
            profit=final_portfolio_value - initial_balance,
            trades_count=test_broker.total_trades,
            final_balance=test_broker.balance,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )

        await self.backtest_repository.set_backtest_result(backtest_result)

    async def update_backtest_status(self, backtest_id: int, status: BacktestStatusModel) -> None:
        db_backtest = await self.backtest_repository.get_backtest(backtest_id)
        if db_backtest is None:
            raise BacktestNotFoundException(backtest_id, backtest_source="PostgreSQL backtest table")

        source_status =BacktestService._get_domain_backtest_status(db_backtest.status)
        is_source_final = BacktestService._is_final_status(source_status)

        if is_source_final and source_status != status:
            raise InvalidStateTransitionException(source_status, status)

        started_at = datetime.now(timezone.utc) if (
                db_backtest.status == BacktestStatus.PENDING and
                status == BacktestStatusModel.RUNNING
        ) else None

        finished_at = datetime.now(timezone.utc) if (
                db_backtest.status == BacktestStatus.RUNNING and
                status == BacktestStatusModel.COMPLETED
        ) else None

        await self.backtest_repository.update_backtest_status(
            backtest_id=backtest_id,
            status=BacktestService._get_db_backtest_status(status),
            started_at=started_at,
            finished_at=finished_at
        )

    async def cancel_backtest(self, backtest_id: int) -> None:
        await self.update_backtest_status(backtest_id=backtest_id, status=BacktestStatusModel.CANCELLED)

    async def get_backtests_for_user(self) -> GetBacktestForUserResponseModel:
        user_email = await self.claim_values_service.get_email()
        user = await self.user_repository.get_user_by_email(user_email)
        if user is None:
            raise UserNotFoundException(user_email=user_email, source="PostgreSQL user table")

        backtests = await self.backtest_repository.get_user_backtests(user.id)
        return GetBacktestForUserResponseModel(
            backtests=list(map(BacktestService._get_domain_backtest, backtests))
        )



    @staticmethod
    def _is_final_status(status: BacktestStatusModel) -> bool:
        return (status == BacktestStatus.COMPLETED or
                status == BacktestStatus.FAILED or
                status == BacktestStatus.CANCELLED)

    @staticmethod
    def _get_domain_backtest(db_backtest: BacktestRecord) -> BacktestModel:
        return BacktestModel(
            id=db_backtest.id,
            user_info=CommonMapper.get_domain_user(db_backtest.user_info),
            model_info=CommonMapper.get_domain_model(db_backtest.model_info),
            started_at=db_backtest.started_at,
            finished_at=db_backtest.finished_at,
            test_period_start=db_backtest.test_period_start,
            test_period_end=db_backtest.test_period_end,
            status=BacktestService._get_domain_backtest_status(db_backtest.status),
            profit=db_backtest.profit,
            trades_count=db_backtest.trades_count,
            initial_balance=db_backtest.initial_balance,
            final_balance=db_backtest.final_balance,
            created_at=db_backtest.created_at,
        )

    @staticmethod
    def _get_domain_backtest_status(db_backtest_status: BacktestStatus) -> BacktestStatusModel:
        match db_backtest_status:
            case BacktestStatus.PENDING: return BacktestStatusModel.PENDING
            case BacktestStatus.FAILED: return BacktestStatusModel.FAILED
            case BacktestStatus.RUNNING: return BacktestStatusModel.RUNNING
            case BacktestStatus.COMPLETED: return BacktestStatusModel.COMPLETED
            case BacktestStatus.CANCELLED: return BacktestStatusModel.CANCELLED
        return BacktestStatusModel.UNKNOWN

    @staticmethod
    def _get_db_backtest_status(domain_backtest_status: BacktestStatusModel) -> BacktestStatus:
        match domain_backtest_status:
            case BacktestStatusModel.PENDING: return BacktestStatus.PENDING
            case BacktestStatusModel.FAILED: return BacktestStatus.FAILED
            case BacktestStatusModel.RUNNING: return BacktestStatus.RUNNING
            case BacktestStatusModel.COMPLETED: return BacktestStatus.COMPLETED
            case BacktestStatusModel.CANCELLED: return BacktestStatus.CANCELLED
        raise ValueError(f"Unknown backtest status for db: {domain_backtest_status}")

    @staticmethod
    def _create_normalizer(config: dict) -> Normalizer:
        if config and 'normalizer_mins' in config and 'normalizer_maxs' in config:
            return Normalizer(
                mins=np.array(config['normalizer_mins']),
                maxs=np.array(config['normalizer_maxs'])
            )
        return Normalizer()