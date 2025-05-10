from dataclasses import dataclass
from app.domain.models.user.UserAssetInfoModel import UserAssetInfoModel


@dataclass(frozen=True)
class GetPortfolioResponseModel:
    ruble_balance: float
    positions: list[UserAssetInfoModel]