import json
import logging
import os
import sys
import torch
import asyncio

from typing import Type
from dataclasses import asdict
from pathlib import Path
from typing import Callable
from dotenv import load_dotenv
from torch.utils.data import DataLoader
from pandas import DataFrame
from app.infrastructure.encoders.DateTimeEncoder import DateTimeEncoder
from dataAccess.PgModelRepository import PgModelRepository
from dataAccess.PgConnectionProvider import PgConnectionProvider
from ml.configuration.FullModelInfo import FullModelInfo
from ml.SequenceDataset import SequenceDataset
from ml.TInvestDataProvider import TInvestDataProvider
from ml.dataAugmentation.Normalizer import Normalizer


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)


class TrainingPipeline:
    def __init__(
            self,
            training_configuration,
            model_info: FullModelInfo,
            model_cls: Type[torch.nn.Module],
            training_func: Callable,
            invest_api_key: str
    ):
        self.logger = logging.getLogger("[ONE_MINUTE_PIPELINE]")
        self.scaler = Normalizer()
        self.training_configuration = training_configuration
        self.training_func = training_func
        self.model_cls = model_cls
        self.model_info = model_info
        self.invest_api_key = invest_api_key
        self.pipeline = [
            self.log_configuration,
            self.fetch_training_data,
            self.preprocess_training_data,
            self.setup_dataset,
            self.setup_model,
            self.train_model,
            self.persist_model
        ]

        load_dotenv()
        pg_connection_provider = PgConnectionProvider(
            username=os.getenv('PYTHON_DB_USER'),
            password=os.getenv('PYTHON_DB_PASSWORD'),
            host=os.getenv('PYTHON_DB_HOST'),
            port=int(os.getenv('PYTHON_DB_PORT')),
            db=os.getenv('PYTHON_DB_NAME')
        )
        self.model_repository = PgModelRepository(
            connection_provider=pg_connection_provider
        )

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
                raise

    def reset(self):
        self.model = None
        self.training_df = None
        self.train_loader = None
        self.test_loader = None

    def log_configuration(self) -> None:
        logger = self.logger
        cuda_available = torch.cuda.is_available()
        logger.info(
            f"Pytorch configuration: \n"
            f"PyTorch version: {torch.__version__}\n"
            f"CUDA available: {torch.cuda.is_available()}\n"
        )
        if cuda_available:
            logger.info(
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
            f"Model configuration: \n"
            f"{self.model_info}"
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
        df = self.training_df.copy()

        df['prev_open'] = df['open'].shift(1)
        df['prev_close'] = df['close'].shift(1)
        df = df.dropna()

        features = df[['close']].values
        normalized_features = self.scaler.fit_transform(features)

        self.model_info.normalizer_maxs = list(self.scaler.maxs)
        self.model_info.normalizer_mins = list(self.scaler.mins)

        self.training_df = df.assign(
            normalized_features=list(normalized_features)
        )


    def setup_dataset(self) -> None:
        training_dataset = SequenceDataset(self.training_df, seq_length=self.training_configuration.sequence_length)
        train_size = int(0.8 * len(training_dataset))
        test_size = len(training_dataset) - train_size
        train_dataset, test_dataset = torch.utils.data.random_split(training_dataset, [train_size, test_size])

        self.train_loader = DataLoader(train_dataset, batch_size=self.training_configuration.batch_size, shuffle=True)
        self.test_loader = DataLoader(test_dataset, batch_size=self.training_configuration.batch_size, shuffle=False)

    def setup_model(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model_cls(self.model_info).to(self.device)

    def train_model(self) -> None:
        logger = logging.getLogger("[ONE_MINUTE_TRAIN]")
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.training_configuration.learning_rate)
        self.training_func(
            model=self.model,
            training_configuration=self.training_configuration,
            train_loader=self.train_loader,
            test_loader=self.test_loader,
            scaler=self.scaler,
            device=self.device,
            logger=logger,
            optimizer=optimizer,
        )

    async def persist_model(self) -> None:
        model_name = self.model_info.name
        config_dict = asdict(self.model_info)

        await self.model_repository.add_model(
            instrument_id=self.model_info.instrument_id,
            name=model_name,
            model_type=self.model_info.model_type,
            model=self.model,
            configuration=json.dumps(config_dict, indent=4, cls=DateTimeEncoder)
        )