import asyncio
from datetime import datetime, timedelta, timezone, time
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import asyncio

from datetime import datetime, timedelta, timezone, time

from ml.TInvestDataProvider import TInvestDataProvider
from ml.data.ApiBroker import ApiBroker
from ml.data.ApiCandleGenerator import ApiCandleGenerator
from ml.data.HistoryCandleGenerator import HistoryCandleGenerator
from ml.data.PresetTradingWindowManager import PresetTradingWindowManager
from ml.data.RetryPolicy import RetryPolicy
from ml.data.TestBroker import TestBroker
from ml.data.configuration.BackoffStrategy import BackoffStrategy
from ml.data.configuration.RetryPolicyConfiguration import RetryPolicyConfiguration
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from ml.runner.StockTrader import StockTrader
from ml.runner.configuration.TradingConfiguration import TradingConfiguration
import torch
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

async def run_single_test(invest_api_key, SBER_INSTRUMENT_ID, config,
                          sell_signal, buy_signal, test_start, test_end, test_candle_source):
    """Run a single test with given signal parameters and return the results."""
    test_trading_window_manager = PresetTradingWindowManager(
        trading_windows=[(time(hour=7, minute=0, second=0, microsecond=0),
                          time(hour=16, minute=50, second=0, microsecond=0))],
    )

    test_broker = TestBroker(
        start_balance=100000,
        lot_size=10,
        commission=0.0005,
    )

    test_trading_config = TradingConfiguration(
        sell_signal=sell_signal,
        buy_signal=buy_signal,
    )

    test_trader = StockTrader(
        model_configuration=config,
        trading_configuration=test_trading_config,
        device="cuda" if torch.cuda.is_available() else "cpu",
        invest_api_key=invest_api_key,
        instrument_id=SBER_INSTRUMENT_ID,
        candle_source=test_candle_source,
        broker=test_broker,
        trading_window_manager=test_trading_window_manager,
    )

    test_trader.load(
        "../savedModels/LSTM_ONE_MINUTE_LAST.pth",
        "../savedModels/LSTM_ONE_MINUTE_normalizer.txt",
    )

    try:
        await test_trader.start_trading()
        initial_balance = 100000
        final_portfolio_value = test_broker.portfolio_value
        returns_pct = ((final_portfolio_value - initial_balance) / initial_balance) * 100

        return {
            'sell_signal': sell_signal,
            'buy_signal': buy_signal,
            'final_balance': test_broker.balance,
            'shares': test_broker.shares,
            'portfolio_value': final_portfolio_value,
            'returns_pct': returns_pct,
            'total_trades': test_broker.total_trades
        }
    except KeyboardInterrupt:
        return None


async def perform_grid_search():
    load_dotenv()
    invest_api_key = os.environ.get("INVEST_TOKEN")
    account_id = os.environ.get("ACCOUNT_ID")
    SBER_INSTRUMENT_ID = "e6123145-9665-43e0-8413-cd61b8aa9b13"

    config = LstmConfiguration(
        input_size=1,
        hidden_layer_size=32,
        num_layers=1,
        output_size=1
    )

    # Define the parameter grid
    sell_signals = np.linspace(0.0009, 0.0011, 5)  # 10 values from 0.0005 to 0.002
    buy_signals = np.linspace(0.0005, 0.0009, 5)  # 10 values from 0.0005 to 0.002

    # Prepare test period
    now = datetime.now(timezone.utc)
    test_start = now - timedelta(days=100)
    test_end = now - timedelta(days=0)

    results = []

    test_candle_source = HistoryCandleGenerator(
        invest_api_key=invest_api_key,
        start_timestamp=test_start,
        end_timestamp=test_end,
        instrument_id=SBER_INSTRUMENT_ID
    )
    await test_candle_source.load_data()

    for sell_signal in sell_signals:
        for buy_signal in buy_signals:
            # Ensure buy signal is less than sell signal to prevent arbitrage
            # if buy_signal >= sell_signal:
            #     continue

            print(f"Testing sell_signal={sell_signal:.6f}, buy_signal={buy_signal:.6f}")
            result = await run_single_test(
                invest_api_key, SBER_INSTRUMENT_ID, config,
                sell_signal, buy_signal, test_start, test_end,
                test_candle_source
            )
            if result:
                results.append(result)
                print(f"Results: {result['returns_pct']:.2f}% return")

    # Convert results to DataFrame
    df = pd.DataFrame(results)

    # Pivot for heatmap
    heatmap_data = df.pivot(index='sell_signal', columns='buy_signal', values='returns_pct')

    # Plot heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap='RdYlGn',
                cbar_kws={'label': 'Returns %'})
    plt.title('Returns by Sell/Buy Signal Combinations')
    plt.xlabel('Buy Signal')
    plt.ylabel('Sell Signal')
    plt.tight_layout()
    plt.savefig('trading_signal_heatmap.png')
    plt.show()

    # Save results to CSV
    df.to_csv('grid_search_results.csv', index=False)

    # Print best performing combination
    best_idx = df['returns_pct'].idxmax()
    best = df.loc[best_idx]
    print("\nBest performing combination:")
    print(f"Sell signal: {best['sell_signal']:.6f}")
    print(f"Buy signal: {best['buy_signal']:.6f}")
    print(f"Returns: {best['returns_pct']:.2f}%")
    print(f"Total trades: {best['total_trades']}")


if __name__ == "__main__":
    asyncio.run(perform_grid_search())