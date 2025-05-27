from enum import Enum


class BusinessErrorCode(Enum):
    Unknown = 0
    ModelNotFound = 1
    ExecutionNotFound = 2
    InvalidExecutionStateTransition = 3
    UserNotFound = 4
    BacktestNotFound = 5
    BacktestAlreadyQueued = 6
    InvalidBacktestStateTransition = 7
    InvestApiKeyNotSet = 7
