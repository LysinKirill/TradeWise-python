import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import logging
import sys
import pandas as pd
import seaborn as sns


from datetime import datetime
from itertools import product
from ml.TInvestDataProvider import TInvestDataProvider
from ml.dataAugmentation.Normalizer import Normalizer
from ml.oneMinute.LSTM.simulation.GridSearchResult import GridSearchResult
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
            scaler: Normalizer,
            instrument_id: str
    ):
        self.logger = logging.getLogger("[SIMULATOR]")
        self.model = model
        self.invest_api_key = invest_api_key
        self.instrument_id = instrument_id
        self.scaler = scaler
        self.close_data: np.ndarray | None = None
        self.lot_size: int | None = None
        self.last_simulation_stats: SimulationStatistics | None = None
        self.grid_search_result: GridSearchResult | None = None
        return

    async def load_data(
            self,
            start_timestamp_utc: datetime,
            end_timestamp_utc: datetime
    ) -> None:
        provider = TInvestDataProvider(api_key=self.invest_api_key)
        df = await provider.load_candle_data_for_period(
            period_start_utc=start_timestamp_utc,
            period_end_utc=end_timestamp_utc,
            instrument_id=self.instrument_id
        )

        self.lot_size = (await provider.get_instrument_info(instrument_id=self.instrument_id)).lot
        await provider.close()
        self.close_data = df['close'].to_numpy()

    async def simulate_trading(
            self,
            device,
            start_timestamp_utc: datetime,
            end_timestamp_utc: datetime,
            initial_balance=10000,
            commission=0.0005,
            lookback=16,
            buy_signal=0.001,
            sell_signal=0.003
    ) -> SimulationResult:
        await self.load_data(
            start_timestamp_utc=start_timestamp_utc,
            end_timestamp_utc=end_timestamp_utc
        )

        return await self.simulate_trading_with_stored_data(
            device=device,
            initial_balance=initial_balance,
            commission=commission,
            lookback=lookback,
            buy_signal=buy_signal,
            sell_signal=sell_signal
        )

    async def simulate_trading_with_stored_data(
        self,
        device,
        initial_balance: float=10000,
        commission: float=0.0005,
        lookback: int=16,
        buy_signal: float=0.001,
        sell_signal: float=0.003
    ) -> SimulationResult:
        self.model.eval()

        balance = initial_balance
        shares_owned = 0
        balance_history = [balance]
        total_value_history = [balance]
        price_history = []
        buy_signals = []
        sell_signals = []
        commission_paid_total = 0

        normalized_data = self.scaler.transform(self.close_data.reshape(-1, 1)).flatten()

        for i in range(lookback, len(self.close_data) - 1):
            current_price = self.close_data[i]
            price_history.append(current_price)

            seq = normalized_data[i - lookback:i].reshape(1, lookback, 1)
            seq = torch.FloatTensor(seq).to(device)

            with torch.no_grad():
                pred = self.model(seq).cpu().numpy()[0]
                pred_price = self.scaler.inverse_transform(np.array([[pred]]))[0][0]

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


    async def grid_search_trading_params(
        self,
        device: str,
        buy_thresholds: np.ndarray,
        sell_thresholds: np.ndarray,
        period_start_utc: datetime | None,
        period_end_utc: datetime | None,
        initial_balance: float = 10000,
        verbose: bool = True
    ) -> GridSearchResult:
        if period_start_utc is None or period_end_utc is None:
            if period_start_utc is not None or period_end_utc is not None:
                raise ValueError("Period start and period end have to either both be None or both be present")
            self.logger.warning("Using previously set period start and period end for grid search.")
        else:
            await self.load_data(
                start_timestamp_utc=period_start_utc,
                end_timestamp_utc=period_end_utc,
            )

        results = []

        for buy_signal, sell_signal in product(buy_thresholds, sell_thresholds):
            if verbose:
                self.logger.info(f"Processing signal thresholds: {buy_signal=:.4f}, {sell_signal=:.4f}. ")

            try:
                simulation_result = await self.simulate_trading_with_stored_data(
                    device=device,
                    initial_balance=initial_balance,
                    commission=0.0005,
                    lookback=16,
                    buy_signal=buy_signal,
                    sell_signal=sell_signal
                )

                returns_pct = simulation_result.total_return * 100

                if verbose:
                    self.logger.info(f"Returns percentage: {returns_pct=:.4f}%\t[{'↓' if returns_pct < 0 else '↑'}]")

                results.append({
                    'buy_signal': buy_signal,
                    'sell_signal': sell_signal,
                    'returns_pct': returns_pct,
                    'signal_ratio': sell_signal / buy_signal
                })

            except Exception as e:
                self.logger.error(f"Failed for buy={buy_signal:.4f}, sell={sell_signal:.4f}: {str(e)}")


        results_df = pd.DataFrame(results)
        if not results_df.empty:
            best = results_df.loc[results_df['returns_pct'].idxmax()]
            if verbose:
                self.logger.info(f"\nBest parameters: buy={best['buy_signal']:.4f}, sell={best['sell_signal']:.4f}")
                self.logger.info(f"Expected return: {best['returns_pct']:.2f}%")

            result = GridSearchResult(
                search_df=results_df,
                best_buy_signal=best['buy_signal'],
                best_sell_signal=best['sell_signal'],
                best_return_pct=best['returns_pct']
            )
            self.grid_search_result = result
            return result


    def plot_grid_search_results(self) -> None:
        if self.grid_search_result is None:
            self.logger.warning("No grid search results found. Run grid search first.")
            return

        results_df = self.grid_search_result.search_df
        if not results_df.empty:
            plt.figure(figsize=(12, 8))

            pivot_df = results_df.pivot_table(
                values='returns_pct',
                index='buy_signal',
                columns='sell_signal'
            )

            sns.heatmap(
                data=pivot_df,
                annot=True,
                fmt=".1f",
                cmap="RdYlGn",
                cbar_kws={'label': 'Returns (%)'}
            )
            plt.title("Returns by Buy/Sell Thresholds")
            plt.xlabel("Sell Signal Threshold")
            plt.ylabel("Buy Signal Threshold")
            plt.tight_layout()
            plt.show()