import asyncio
import os
import sys
import torch

from typing import Type
from dotenv import load_dotenv
from app.configuration.Settings import Settings
from ml.configuration.FullModelInfo import FullModelInfo
from ml.oneMinute.LSTM.StockPriceLstm import StockPriceLstm
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from ml.oneMinute.LSTM.configuration.TrainingConfiguration import TrainingConfiguration
from ml.oneMinute.LSTM.training.train import train_model
from ml.training.TrainingPipeline import TrainingPipeline
from dataclasses import is_dataclass, fields
from datetime import datetime
from typing import TypeVar

T = TypeVar('T')


def get_model_class_by_type(model_type: str) -> Type[torch.nn.Module]:
    model_type = model_type.lower()
    match model_type:
        case 'lstm': return StockPriceLstm

    raise ValueError(f'Model type {model_type} not recognized')

def get_configuration_class_by_type(model_type: str) -> Type:
    model_type = model_type.lower()
    match model_type:
        case 'lstm': return LstmConfiguration

    raise ValueError(f'Model type {model_type} not recognized')


def load_dataclass(cls: Type[T], data: dict, **field_types) -> T:
    if not is_dataclass(cls):
        raise ValueError(f"{cls.__name__} is not a dataclass")

    converted = {}
    for field in fields(cls):
        if field.name not in data:
            continue

        value = data[field.name]

        try:
            if field.type is datetime:
                converted[field.name] = datetime.fromisoformat(value) if isinstance(value, str) else value

            elif is_dataclass(field.type):
                converted[field.name] = load_dataclass(field.type, value)
            elif is_dataclass(field_types.get(field.name)):
                converted[field.name] = load_dataclass(field_types.get(field.name), value)
            elif hasattr(field.type, "__origin__") and field.type.__origin__ is list:
                if field.type.__args__[0] is float:
                    converted[field.name] = [float(x) for x in value]
                else:
                    converted[field.name] = list(value)

            else:
                converted[field.name] = value

        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to convert field '{field.name}': {str(e)}") from e

    return cls(**converted)


async def main(config_path: str = "./training_settings.json"):
    load_dotenv()
    settings = Settings(config_path)

    invest_api_key = os.environ.get("INVEST_TOKEN")
    training_config = settings.get("TrainingConfiguration")
    full_model_info_settings = settings.get("FullModelInfo")

    config_class = get_configuration_class_by_type(full_model_info_settings['model_type'])
    full_model_info = load_dataclass(
        FullModelInfo,
        settings.get("FullModelInfo"),
        model_configuration=config_class)

    training_configuration = TrainingConfiguration(
        instrument_id=training_config["instrument_id"],
        sequence_length=training_config.get("sequence_length", 16),
        train_period_start_utc=datetime.fromisoformat(training_config["train_period_start"]),
        train_period_end_utc=datetime.fromisoformat(training_config["train_period_end"]),
        batch_size=training_config.get("batch_size", 32),
        epochs=training_config.get("epochs", 20),
        learning_rate=training_config.get("learning_rate", 0.01)
    )

    pipeline = TrainingPipeline(
        training_configuration=training_configuration,
        model_info=full_model_info,
        invest_api_key=invest_api_key,
        model_cls=get_model_class_by_type(full_model_info.model_type),
        training_func=train_model
    )

    try:
        await pipeline.run_pipeline()
        print("Pipeline completed successfully!")
    except Exception as e:
        print(f"Failed to run pipeline: {str(e)}")


if __name__ == '__main__':
    settings_file = "./settings/oneMinute/SBER_one_minute_16_lookback.json"
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if 'pydevd' in sys.modules:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main(settings_file))
        finally:
            loop.close()
    else:
        asyncio.run(main(settings_file))
