from dataclasses import dataclass


@dataclass
class TradingConfiguration:
    sell_signal: float
    buy_signal: float