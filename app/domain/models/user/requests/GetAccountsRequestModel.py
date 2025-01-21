from dataclasses import dataclass

from app.domain.models.user import AccountStatusModel


@dataclass(frozen=True)
class GetAccountsRequestModel:
    status: AccountStatusModel
