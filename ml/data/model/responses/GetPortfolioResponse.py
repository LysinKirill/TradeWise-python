from dataclasses import dataclass


@dataclass
class GetPortfolioResponse:
    rub: float
    shares: int