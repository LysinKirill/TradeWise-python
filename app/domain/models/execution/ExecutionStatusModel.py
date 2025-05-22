from enum import Enum


class ExecutionStatusModel(str, Enum):
    UNKNOWN = "unknown"
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'