from app.domain.exceptions.model.ModelNotFoundException import ModelNotFoundException
from app.domain.exceptions.user.UserNotFoundException import UserNotFoundException
from app.domain.models.backtest.requests.EnqueueBacktestRequestModel import EnqueueBacktestRequestModel
from app.domain.models.backtest.responses.EnqueueBacktestResponseModel import EnqueueBacktestResponseModel
from app.domain.services.IBacktestService import IBacktestService
from dataAccess.interfaces.IBacktestRepository import IBacktestRepository
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.interfaces.IUserRepository import IUserRepository


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

        backtest_id = await self.backtest_repository.create_backtest(
            user_id=user.id,
            model_id=model.id,
            allocated_amount=request.initial_balance,
            from_=request.from_,
            to=request.to,
        )

        return EnqueueBacktestResponseModel(backtest_id=backtest_id)

