import logging
import sys
from typing import Callable

import torch
import asyncio

from torch.utils.data import DataLoader
from pandas import DataFrame

from ml.oneMinute.LSTM.configuration.TrainingConfiguration import TrainingConfiguration
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from ml.SequenceDataset import SequenceDataset
from ml.TInvestDataProvider import TInvestDataProvider
from ml.dataAugmentation.Normalizer import Normalizer
from ml.oneMinute.LSTM.StockPriceLstm import StockPriceLstm
from ml.oneMinute.LSTM.training.train import train_model as train_model_internal


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

class TrainingPipeline:
    def __init__(
            self,
            training_configuration: TrainingConfiguration,
            lstm_configuration: LstmConfiguration,
            invest_api_key: str
    ):
        self.logger = logging.getLogger("[LSTM_ONE_MINUTE_PIPELINE]")
        self.scaler = Normalizer()
        self.training_configuration = training_configuration
        self.lstm_configuration = lstm_configuration
        self.invest_api_key = invest_api_key
        self.pipeline = [
            self.log_configuration,
            self.fetch_training_data,
            self.preprocess_training_data,
            self.setup_dataset,
            self.setup_model,
            self.train_model,
        ]
        self.train_loader: DataLoader | None = None
        self.test_loader: DataLoader | None = None
        self.training_df: DataFrame | None = None
        self.device: str | None = None
        self.model: torch.nn.Module | None = None

    async def run_pipeline(self):
        for pipeline_step in self.pipeline:
            try:
                self.logger.info(f"Running {pipeline_step.__name__}")
                if asyncio.iscoroutinefunction(pipeline_step):
                    await pipeline_step()
                else:
                    pipeline_step: Callable[[], None] | None
                    pipeline_step()
            except Exception as e:
                self.logger.error(e)
                self.logger.error(f"Failed to run pipeline step {pipeline_step.__name__}!\n"
                                  f"Resetting pipeline state...")
                self.reset()
                break

    def reset(self):
        self.model = None
        self.training_df = None
        self.train_loader = None
        self.test_loader = None

    def log_configuration(self) -> None:
        logger = self.logger
        logger.info(
            f"Pytorch configuration: \n"
            f"PyTorch version: {torch.__version__}\n"
            f"CUDA available: {torch.cuda.is_available()}\n"
            f"CUDA device count: {torch.cuda.device_count()}\n"
            f"Current CUDA device: {torch.cuda.current_device()}\n"
            f"CUDA device name: {torch.cuda.get_device_name(0)}\n"
            f"_________________________________________________"
        )
        logger.info(
            f"Training configuration: \n"
            f"{self.training_configuration}"
            f"_________________________________________________"
        )
        logger.info(
            f"LSTM configuration: \n"
            f"{self.lstm_configuration}"
            f"_________________________________________________"
        )

    async def fetch_training_data(self) -> None:
        provider = TInvestDataProvider(api_key=self.invest_api_key)
        try:
            config = self.training_configuration
            self.training_df = await provider.load_candle_data_for_period(
                period_start_utc=config.train_period_start_utc,
                period_end_utc=config.train_period_end_utc,
                instrument_id=config.instrument_id
            )
        finally:
            await provider.close()

    def preprocess_training_data(self) -> None:
        self.training_df['close_normalized'] = self.scaler.fit_transform(self.training_df[['close']].values)

    def setup_dataset(self) -> None:
        training_dataset = SequenceDataset(self.training_df, seq_length=self.training_configuration.sequence_length)
        train_size = int(0.8 * len(training_dataset))
        test_size = len(training_dataset) - train_size
        train_dataset, test_dataset = torch.utils.data.random_split(training_dataset, [train_size, test_size])

        self.train_loader = DataLoader(train_dataset, batch_size=self.training_configuration.batch_size, shuffle=True)
        self.test_loader = DataLoader(test_dataset, batch_size=self.training_configuration.batch_size, shuffle=False)

    def setup_model(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = StockPriceLstm(self.lstm_configuration).to(self.device)

    def train_model(self) -> None:
        logger = logging.getLogger("[LSTM_ONE_MINUTE_TRAIN]")
        train_model_internal(
            model=self.model,
            training_configuration=self.training_configuration,
            lstm_configuration=self.lstm_configuration,
            train_loader=self.train_loader,
            test_loader=self.test_loader,
            scaler=self.scaler,
            device=self.device,
            logger=logger,
            save_best_model=True
        )

