from app.domain.BusinessErrorCode import BusinessErrorCode
from app.domain.BusinessException import BusinessException
from app.domain.models.execution.ExecutionStatusModel import ExecutionStatusModel


class InvalidStateTransitionException(BusinessException):
    def __init__(
            self,
            start_state: ExecutionStatusModel,
            end_state: ExecutionStatusModel | None = None,
    ):
        self.start_state = start_state
        self.end_state = end_state
        message = f'Attempted to perform invalid state transition from state {self.start_state}'
        if end_state is not None:
            message += f" to state {end_state}"

        super().__init__(BusinessErrorCode.InvalidExecutionStateTransition, message)

