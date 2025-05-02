from dataclasses import dataclass


@dataclass
class SimulationStatistics:
    price_history: list[float]
    buy_signals: list[tuple[int, float]]
    sell_signals: list[tuple[int, float]]
    total_value_history: list[float]
    balance_history: list[float]
    final_value: float
    returns: float