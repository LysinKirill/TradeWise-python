from torch.utils.data import Dataset

from TrainingConfiguration import LstmTrainingConfiguration
from pandas import DataFrame

from ml.SequenceDataset import SequenceDataset
from ml.TInvestDataProvider import TInvestDataProvider
from ml.dataAugmentation.Normalizer import Normalizer


class TrainingPipeline:
    def __init__(
            self,
            training_configuration: LstmTrainingConfiguration,
            invest_api_key: str
    ):
        self.training_dataset: Dataset | None = None
        self.scaler = Normalizer()
        self.training_df: DataFrame | None = None
        self.configuration = training_configuration
        self.invest_api_key = invest_api_key
        self.pipeline = [
            self.fetch_training_data,
            TrainingPipeline.preprocess_training_data
        ]

    def run_pipeline(self):
        pass

    async def fetch_training_data(self) -> None:
        provider = TInvestDataProvider(api_key=self.invest_api_key)
        try:
            config = self.configuration
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
        self.training_dataset = SequenceDataset(self.training_df, seq_length=self.configuration.sequence_length)



