from dataclasses import dataclass


@dataclass(frozen=True)
class AddInvestApiKeyRequestModel:
    api_key: str
    email: str
