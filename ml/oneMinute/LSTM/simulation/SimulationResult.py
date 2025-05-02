from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationResult:
    initial_balance: float
    final_balance: float
    total_return: float
    annualized_sharpe_ratio: float
    total_trades: int
    commission_paid: float