import torch
from ml.dataAugmentation.Normalizer import Normalizer
from ml.oneMinute.LSTM.StockPriceLstm import StockPriceLstm
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from ml.runner.configuration.TradingConfiguration import TradingConfiguration


class StockTrader:
    def __init__(
        self,
        model_configuration: LstmConfiguration, # TODO: replace with supertype for model configuration
        device: str,
        trading_configuration: TradingConfiguration,
    ):
        self.device = device
        self.model = StockPriceLstm(model_configuration).to(device)
        self.trading_configuration = trading_configuration
        self.scaler: Normalizer | None = None
        return

    def load(
        self,
        saved_model_path: str,
        saved_normalizer_path: str
    ):
        self.model.load_state_dict(torch.load(saved_model_path))
        with open(saved_normalizer_path, 'rb') as f:
            params = list(map(float, f.readline().split()))
            self.scaler = Normalizer(
                min_val=params[0],
                max_val=params[1],
            )


