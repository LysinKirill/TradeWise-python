from enum import Enum


class InstrumentStatType(Enum):
    Unknown = 0
    BollingerBands = 1
    ExponentialMovingAverage = 2
    RelativeStrengthIndex = 3
    MovingAverageConvergenceDivergence = 4
    MovingAverage = 5