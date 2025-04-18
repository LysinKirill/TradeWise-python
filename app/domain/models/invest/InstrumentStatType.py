from enum import Enum


class InstrumentStatType(Enum):
    Unknown = 0
    BollingerBandLower = 1
    BollingerBandMiddle = 2
    BollingerBandUpper = 3
    ExponentialMovingAverage = 4
    RelativeStrengthIndex = 5
    MovingAverageConvergenceDivergence = 6
    MovingAverage = 7