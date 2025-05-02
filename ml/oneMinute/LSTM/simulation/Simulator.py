import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import logging
import sys

from datetime import datetime
from ml.TInvestDataProvider import TInvestDataProvider
from ml.oneMinute.LSTM.simulation.SimulationResult import SimulationResult
from ml.oneMinute.LSTM.simulation.SimulationStatistics import SimulationStatistics


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)


class TradingSimulator:
    def __init__(
            self,
            invest_api_key: str,
            model: nn.Module,
    ):
        self.logger = logging.getLogger("[SIMULATOR]")
        self.model = model
        self.invest_api_key = invest_api_key
        self.close_data: np.ndarray | None = None
        self.lot_size: int | None = None
        self.last_simulation_stats: SimulationStatistics | None = None
        return

    async def load_data(
            self,
            instrument_id: str,
            start_timestamp_utc: datetime,
            end_timestamp_utc: datetime
    ) -> None:
        provider = TInvestDataProvider(api_key=self.invest_api_key)
        try:
            df = await provider.load_candle_data_for_period(
                period_start_utc=start_timestamp_utc,
                period_end_utc=end_timestamp_utc,
                instrument_id=instrument_id
            )

            self.lot_size = (await provider.get_instrument_info(instrument_id=instrument_id)).lot
            await provider.close()
            self.close_data = df['close'].to_numpy()
        finally:
            await provider.close()


    async def simulate_trading(
        self,
        scaler,
        device,
        instrument_id: str,
        start_timestamp_utc: datetime,
        end_timestamp_utc: datetime,
        initial_balance=10000,
        commission=0.0005,
        lookback=16,
        buy_signal=0.001,
        sell_signal=0.003
    ) -> SimulationResult:
        await self.load_data(
            instrument_id=instrument_id,
            start_timestamp_utc=start_timestamp_utc,
            end_timestamp_utc=end_timestamp_utc
        )

        self.model.eval()

        balance = initial_balance
        shares_owned = 0
        balance_history = [balance]
        total_value_history = [balance]
        price_history = []
        buy_signals = []
        sell_signals = []
        commission_paid_total = 0

        normalized_data = scaler.transform(self.close_data.reshape(-1, 1)).flatten()

        for i in range(lookback, len(self.close_data) - 1):
            current_price = self.close_data[i]
            price_history.append(current_price)

            seq = normalized_data[i - lookback:i].reshape(1, lookback, 1)
            seq = torch.FloatTensor(seq).to(device)

            with torch.no_grad():
                pred = self.model(seq).cpu().numpy()[0]
                pred_price = scaler.inverse_transform(np.array([[pred]]))[0][0]

            expected_return = (pred_price - current_price) / current_price

            # Trading decision logic - SIMPLIFIED VERSION
            if expected_return > buy_signal:  # Strong buy signal
                if shares_owned == 0:  # Only buy if we don't own shares
                    # Calculate how many shares we can buy
                    max_shares = (balance // (current_price * self.lot_size * (1 + commission))) * self.lot_size
                    shares_owned = max_shares
                    commission_paid = shares_owned * (current_price * commission)
                    balance = balance - (shares_owned * current_price + commission)
                    commission_paid_total += commission_paid
                    buy_signals.append((i - lookback, current_price))

            elif expected_return < -sell_signal:  # Sell signal
                if shares_owned > 0:  # Only sell if we own shares
                    # Sell all shares
                    commission_paid = shares_owned * current_price * commission
                    sale_value = shares_owned * current_price - commission_paid
                    commission_paid_total += commission_paid
                    balance += sale_value
                    shares_owned = 0
                    sell_signals.append((i - lookback, current_price))

            # Calculate current portfolio value
            position_value = shares_owned * current_price
            total_value = balance + position_value

            # Record history
            balance_history.append(balance)
            total_value_history.append(total_value)

        # Final portfolio value (sell any remaining shares)
        if shares_owned > 0:
            final_value = balance + (shares_owned * self.close_data[-1] * (1 - commission))
        else:
            final_value = balance

        returns = (final_value - initial_balance) / initial_balance

        # Calculate metrics
        returns_series = np.array(total_value_history) / initial_balance - 1
        std_dev = np.std(returns_series)
        sharpe_ratio = np.mean(returns_series) / std_dev * np.sqrt(252 * 24 * 60) if std_dev > 0 else 0

        self.last_simulation_stats = SimulationStatistics(
            price_history=price_history,
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            total_value_history=total_value_history,
            balance_history=balance_history,
            final_value=final_value,
            returns=returns,
        )

        simulation_results = SimulationResult(
            initial_balance=initial_balance,
            final_balance=final_value,
            total_return=returns,
            annualized_sharpe_ratio=sharpe_ratio,
            total_trades=len(buy_signals) + len(sell_signals),
            commission_paid=commission_paid_total,
        )

        self.logger.info("=== Trading Simulation Results ===")
        self.logger.info(simulation_results)
        return simulation_results

    def plot_simulation_results(self):
        if self.last_simulation_stats is None:
            self.logger.warning("No simulation statistics available. Run simulate_trading() first.")

        stats = self.last_simulation_stats
        #plt.figure(figsize=(14, 10))
        ax1 = plt.subplot(2, 1, 1)
        ax1.plot(stats.price_history, label='Price', color='blue', alpha=0.7)

        # Plot buy/sell signals
        if stats.buy_signals:
            buy_x, buy_y = zip(*stats.buy_signals)
            ax1.scatter(buy_x, buy_y, color='green', marker='^', s=100, label='Buy', alpha=0.8)

        if stats.sell_signals:
            sell_x, sell_y = zip(*stats.sell_signals)
            ax1.scatter(sell_x, sell_y, color='red', marker='v', s=100, label='Sell', alpha=0.8)

        ax1.set_title('Price with Buy/Sell Signals')
        ax1.set_ylabel('Price ($)')
        ax1.legend()
        ax1.grid(True)

        # Plot 2: Portfolio value
        ax2 = plt.subplot(2, 1, 2)
        ax2.plot(stats.total_value_history, label='Total Portfolio Value', color='purple')
        ax2.plot(stats.balance_history, label='Cash Balance', color='orange', linestyle='--')

        # Mark buy/sell points on value plot using the same indices
        if stats.buy_signals:
            buy_x, _ = zip(*stats.buy_signals)
            buy_values = [stats.total_value_history[x] for x in buy_x]
            ax2.scatter(buy_x, buy_values, color='green', marker='^', s=100, alpha=0.8)

        if stats.sell_signals:
            sell_x, _ = zip(*stats.sell_signals)
            sell_values = [stats.total_value_history[x] for x in sell_x]
            ax2.scatter(sell_x, sell_values, color='red', marker='v', s=100, alpha=0.8)

        ax2.set_title(f'Portfolio Value (Final: ${stats.final_value:,.2f}, Return: {stats.returns:.2%})')
        ax2.set_xlabel('Minutes')
        ax2.set_ylabel('Value ($)')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        plt.show()