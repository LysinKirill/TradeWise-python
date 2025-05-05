from enum import Enum


class BackoffStrategy(Enum):
    Fixed = 1
    Linear = 2
    Exponential = 3