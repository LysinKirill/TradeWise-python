import asyncio
import os
import sys
import torch
import argparse
from typing import Type, List
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
from pathlib import Path

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


async def train_for_config(config_path: str):
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
        print(f"Pipeline completed successfully for {config_path}!")
    except Exception as e:
        print(f"Failed to run pipeline for {config_path}: {str(e)}")


async def main(config_paths: List[str]):
    for config_path in config_paths:
        print(f"\nStarting training for config: {config_path}")
        await train_for_config(config_path)


def get_config_files(directory: str, limit: int = None) -> List[str]:
    path = Path(directory)
    config_files = sorted([str(f) for f in path.glob('*.json')])
    if limit is not None and limit > 0:
        config_files = config_files[:limit]
    return config_files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run training for multiple config files.')
    parser.add_argument('--config-dir', type=str, default="./ml/training/settings/oneMinute",
                        help='Directory containing config files')
    parser.add_argument('--num-models', type=int, default=None,
                        help='Number of models to train (uses first N config files)')
    parser.add_argument('--config-files', type=str, nargs='*',
                        help='Specific config files to use (overrides config-dir and num-models)')

    args = parser.parse_args()
    print(args.config_dir, args.num_models)

    if args.config_files:
        config_files = args.config_files
    else:
        config_files = get_config_files(args.config_dir, args.num_models)

    if not config_files:
        print("No configuration files found!")
        sys.exit(1)

    print(f"Running training for {len(config_files)} config files:")
    for cf in config_files:
        print(f" - {cf}")

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if 'pydevd' in sys.modules:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main(config_files))
        finally:
            loop.close()
    else:
        asyncio.run(main(config_files))