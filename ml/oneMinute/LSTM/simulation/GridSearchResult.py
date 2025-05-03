from pandas import DataFrame
from dataclasses import dataclass


@dataclass
class GridSearchResult:
    search_df: DataFrame
    best_buy_signal: float
    best_sell_signal: float
    best_return_pct: float
