from dataclasses import dataclass


@dataclass
class TradingConfiguration:
    sell_signal: float
    buy_signal: float
    stop_loss: float | None
    take_profit: float | None