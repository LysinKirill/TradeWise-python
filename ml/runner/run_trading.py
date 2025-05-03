import asyncio

from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from ml.runner.TestTrader import StockTrader
from ml.runner.configuration.TradingConfiguration import TradingConfiguration
import torch
from grpc import aio, ssl_channel_credentials
import matplotlib.pyplot as plt


async def main():
    invest_api_key = input("Enter Invest API key: ")
    account_id = input("Enter Invest account ID: ")

    SBER_INSTRUMENT_ID = "e6123145-9665-43e0-8413-cd61b8aa9b13"
    SBER_FIGI = "BBG004730N88"

    config = LstmConfiguration(
        input_size=1,
        hidden_layer_size=32,
        num_layers=1,
        criterion=torch.nn.MSELoss(),
        output_size=1
    )

    trading_config = TradingConfiguration(
        sell_signal=0.0012,
        buy_signal=0.0013,
    )

    channel = aio.secure_channel("invest-public-api.tinkoff.ru:443",
                                 ssl_channel_credentials())

    trader = StockTrader(
        model_configuration=config,
        trading_configuration=trading_config,
        device="cuda" if torch.cuda.is_available() else "cpu",
        invest_api_key=invest_api_key,
        instrument_id=SBER_INSTRUMENT_ID,
        account_id=account_id,
        figi=SBER_FIGI,
        lot_size=10,
        channel=channel
    )

    trader.load(
        "../savedModels/LSTM_ONE_MINUTE.pth",
        "../savedModels/LSTM_ONE_MINUTE_normalizer.txt",
    )

    trader.init_plot()

    try:
        await trader.start_trading()
    except KeyboardInterrupt:
        pass
    finally:
        plt.ioff()
        plt.show()  # Keep plot open after stopping


if __name__ == "__main__":
    asyncio.run(main())