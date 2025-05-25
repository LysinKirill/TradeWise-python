from app.domain.BusinessErrorCode import BusinessErrorCode
from app.domain.BusinessException import BusinessException


class BacktestNotFoundException(BusinessException):
    def __init__(
            self,
            backtest_id: int,
            backtest_source: str | None = None
    ):
        message = f'Backtest {backtest_id} not found' if not backtest_source else f'Execution {backtest_id} not found in source {backtest_source}'
        super().__init__(BusinessErrorCode.BacktestNotFound, message)
