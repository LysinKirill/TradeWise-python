from app.domain.exceptions.backtest.BacktestAlreadyQueuedException import BacktestAlreadyQueuedException
from app.domain.exceptions.backtest.BacktestNotFoundException import BacktestNotFoundException
from app.domain.exceptions.model.ModelNotFoundException import ModelNotFoundException
from app.domain.exceptions.user.UserNotFoundException import UserNotFoundException
from app.domain.models.backtest.BacktestModel import BacktestModel
from app.domain.models.backtest.BacktestStatusModel import BacktestStatusModel
from app.domain.models.backtest.requests.EnqueueBacktestRequestModel import EnqueueBacktestRequestModel
from app.domain.models.backtest.responses.EnqueueBacktestResponseModel import EnqueueBacktestResponseModel
from app.domain.services.IBacktestService import IBacktestService
from app.mappers.domain_dal.CommonMapper import CommonMapper
from dataAccess.interfaces.IBacktestRepository import IBacktestRepository
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.interfaces.IUserRepository import IUserRepository
from dataAccess.models.backtest.BacktestRecord import BacktestRecord
from dataAccess.models.backtest.BacktestStatus import BacktestStatus


class BacktestService(IBacktestService):
    def __init__(
            self,
            backtest_repository: IBacktestRepository,
            user_repository: IUserRepository,
            model_repository: IModelRepository,
    ):
        self.backtest_repository = backtest_repository
        self.user_repository = user_repository
        self.model_repository = model_repository


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
        return BacktestStatusModel.UNKNOWN
