from dataclasses import dataclass


@dataclass(frozen=True)
class UserInfoModel:
    id: int
    email: str
    invest_api_key: str | None
    invest_account_id: str | None