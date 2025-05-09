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


async def main():
    load_dotenv()
    invest_api_key = os.environ.get("INVEST_TOKEN")
    account_id = os.environ.get("ACCOUNT_ID")
    #invest_api_key = input("Enter Invest API key: ")
    #account_id = input("Enter Invest account ID: ")

    SBER_INSTRUMENT_ID = "e6123145-9665-43e0-8413-cd61b8aa9b13"
    START_BALANCE = 100000
    config = LstmConfiguration(
        input_size=1,
        hidden_layer_size=32,
        num_layers=1,
        output_size=1
    )

    trading_config = TradingConfiguration(
        # sell_signal=0.0007,
        # buy_signal=0.0006,
        sell_signal= 0.0009,
        buy_signal= 0.0008
    )

    invest_data_provider = TInvestDataProvider(invest_api_key)

    retry_policy_configuration = RetryPolicyConfiguration(
        initial_delay_in_seconds=5,
        allowed_attempts=3,
        backoff_strategy=BackoffStrategy.Linear
    )

    retry_policy = RetryPolicy(retry_policy_configuration)

    candle_source_one_minute_api = ApiCandleGenerator(
        data_provider=invest_data_provider,
        fetch_delay_in_seconds=60,
        retry_policy=retry_policy
    )

    broker = ApiBroker(
        invest_api_key=invest_api_key,
        account_id=account_id,
        instrument_id=SBER_INSTRUMENT_ID,
    )

### -----------------------------TEST-------------------------------
    #now = datetime(year=2025, month=5, day=4, hour=12, minute=0, second=0, microsecond=0)
    now = datetime.now(timezone.utc)
    test_start = now - timedelta(days=60)
    test_end = now - timedelta(days=0)

    test_trading_window_manager = PresetTradingWindowManager(
        trading_windows=[(time(hour=7, minute=0, second=0, microsecond=0), time(hour=16, minute=50, second=0, microsecond=0))],
    )

    test_candle_source = HistoryCandleGenerator(
        invest_api_key=invest_api_key,
        start_timestamp=test_start,
        end_timestamp=test_end,
        instrument_id=SBER_INSTRUMENT_ID
    )
    await test_candle_source.load_data()
    test_broker = TestBroker(
        start_balance=START_BALANCE,
        lot_size=10,
        commission=0.0005,
    )

    test_trading_config = TradingConfiguration(
        sell_signal= 0.0009,
        buy_signal= 0.0008,
        take_profit=0.005
    )

    #class Sus: pass
    #mock_window_manager = Sus()
    #mock_window_manager.check_trade_available = lambda *args, **kwargs: True



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

### -----------------------------TEST-------------------------------



    trader = StockTrader(
        model_configuration=config,
        trading_configuration=trading_config,
        device="cuda" if torch.cuda.is_available() else "cpu",
        invest_api_key=invest_api_key,
        instrument_id=SBER_INSTRUMENT_ID,
        candle_source=candle_source_one_minute_api,
        broker=broker,
        trading_window_manager=test_trading_window_manager
    )

    test_trader.load(
        "../savedModels/LSTM_ONE_MINUTE_LAST.pth",
        "../savedModels/LSTM_ONE_MINUTE_normalizer.txt",
    )

    try:
        await test_trader.start_trading()
        print(f"{test_broker.total_trades = }")
        print(f"{test_broker.balance = }")
        print(f"{test_broker.shares = }")
        print(f"{test_broker.portfolio_value = }")
        print(f"{test_broker.portfolio_value = }")
        returns = (test_broker.portfolio_value - START_BALANCE) / START_BALANCE
        print(f"returns percentage = {returns * 100:.2f}%")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())