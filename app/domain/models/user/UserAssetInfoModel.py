from dataclasses import dataclass


@dataclass(frozen=True)
class UserAssetInfoModel:
    instrument_id: str
    quantity: int
    ticker: str
    daily_yield: float
    current_price: float
