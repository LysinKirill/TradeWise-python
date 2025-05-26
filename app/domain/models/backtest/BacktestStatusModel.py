from enum import Enum


class BacktestStatusModel(str, Enum):
    UNKNOWN = "unknown"
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'