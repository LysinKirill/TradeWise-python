from enum import Enum


class AccountAccessLevelModel(Enum):
    Unspecified = 0
    FullAccess = 1
    ReadOnly = 2
    NoAccess = 3
