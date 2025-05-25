from app.domain.BusinessErrorCode import BusinessErrorCode
from app.domain.BusinessException import BusinessException


class BacktestAlreadyQueuedException(BusinessException):
    def __init__(
            self,
            user_id: int,
            backtest_ids: list[int],
    ):
        message = f'There are already backtests (ids: {backtest_ids}) for user with Id = {user_id} queued. Only one backtest can be queued.'
        super().__init__(BusinessErrorCode.BacktestAlreadyQueued, message)
