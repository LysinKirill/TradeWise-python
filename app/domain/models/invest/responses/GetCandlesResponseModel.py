from dataclasses import dataclass
from app.domain.models.invest.CandleModel import CandleModel


@dataclass(frozen=True)
class GetCandlesResponseModel:
    candles: list[CandleModel]