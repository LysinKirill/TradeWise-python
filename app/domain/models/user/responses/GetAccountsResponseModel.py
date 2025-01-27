from dataclasses import dataclass

from app.domain.models.user import AccountInfoModel


@dataclass(frozen=True)
class GetAccountsResponseModel:
    accounts: list[AccountInfoModel]
