from enum import Enum


class BusinessErrorCode(Enum):
    Unknown = 0
    ModelNotFound = 1
    ExecutionNotFound = 2
    InvalidExecutionStateTransition = 3
    UserNotFound = 4
