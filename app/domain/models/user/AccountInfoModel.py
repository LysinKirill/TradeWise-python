from dataclasses import dataclass
from datetime import datetime

from . import (
    AccountTypeModel,
    AccountStatusModel,
    AccountAccessLevelModel
)


@dataclass(frozen=True)
class AccountInfoModel:
    id: str
    type: AccountTypeModel.AccountTypeModel
    name: str
    status: AccountStatusModel.AccountStatusModel
    opened_date: datetime
    closed_date: datetime
    access_level: AccountAccessLevelModel.AccountAccessLevelModel
