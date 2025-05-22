from app.domain.BusinessErrorCode import BusinessErrorCode
from app.domain.BusinessException import BusinessException


class ExecutionNotFoundException(BusinessException):
    def __init__(
            self,
            execution_id: int,
            execution_source: str | None = None
    ):
        message = f'Execution {execution_id} not found' if not execution_source else f'Execution {execution_id} not found in source {execution_source}'
        super().__init__(BusinessErrorCode.ExecutionNotFound, message)