import io
import json
from dataclasses import is_dataclass, fields
from datetime import datetime

import torch
import copy
from pydapper.commands import CommandsAsync
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider
from dataAccess.models.model.GetAllModelsInfo import GetAllModelsInfo
from dataAccess.models.model.GetModelResponse import GetModelResponse
from typing import Any, Type
from dataAccess.models.model.ShortModelInfo import ShortModelInfo
from ml.configuration.FullModelInfo import FullModelInfo
from ml.oneMinute.LSTM.StockPriceLstm import StockPriceLstm
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from typing import TypeVar

T = TypeVar('T')


class PgModelRepository(IModelRepository):
    def __init__(self, connection_provider: IPgConnectionProvider):
        self.connection_provider = connection_provider
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    async def add_model(
            self,
            instrument_id: str,
            name: str,
            model_type: str,
            model: torch.nn.Module,
            configuration: Any | None = None
    ) -> int:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            buffer = io.BytesIO()
            torch.save(model.state_dict(), buffer)
            model_bytes = buffer.getvalue()

            model_id = await commands.execute_scalar_async(
                '''
                INSERT INTO models (
                    instrument_id, 
                    name, 
                    type, 
                    model_bytes, 
                    config
                )
                VALUES (
                    ?instrument_id?, 
                    ?name?, 
                    ?type?, 
                    ?model_bytes?, 
                    ?config?
                )
                RETURNING id;
                ''',
                param={
                    "instrument_id": instrument_id,
                    "name": name,
                    "type": model_type,
                    "model_bytes": model_bytes,
                    "config": json.dumps(configuration) if configuration else None
                }
            )
            return model_id

    async def get_model(
            self,
            model_id: int,
            model_for_init: torch.nn.Module | None
    ) -> GetModelResponse | None:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            record = await commands.query_first_async(
                '''
                SELECT
                    id,
                    instrument_id, 
                    name, 
                    type as model_type,
                    created_at,
                    model_bytes, 
                    config
                FROM models 
                WHERE id = ?model_id?
                ''',
                param={"model_id": model_id}
            )

            if not record:
                return None

            if model_for_init is None:
                config_class = PgModelRepository._get_configuration_class_by_type(record['model_type'])
                full_model_info_settings = config_class.from_json(record['config']) if record.get('config') else None
                full_model_info = PgModelRepository._load_dataclass(
                    FullModelInfo,
                    full_model_info_settings,
                    model_configuration=config_class)
                model_cls = PgModelRepository._get_model_class_by_type(record['model_type'])
                model_for_init = model_cls(full_model_info).to(self.device)



            model_copy = copy.deepcopy(model_for_init)

            buffer = io.BytesIO(record['model_bytes'])
            state_dict = torch.load(buffer, map_location=torch.device('cpu'))
            model_copy.load_state_dict(state_dict)

            config = json.loads(record['config']) if 'config' in record.keys() else None

            return GetModelResponse(
                id=record['id'],
                instrument_id=record['instrument_id'],
                name=record['name'],
                model_type=record['model_type'],
                model=model_copy,
                config=config,
                created_at=record['created_at']
            )

    async def get_all_models_info(self) -> GetAllModelsInfo:
        async with (self.connection_provider.get_connection() as commands):
            commands: CommandsAsync

            records = await commands.query_async(
                '''
                SELECT 
                    id,
                    instrument_id,
                    name,
                    type as model_type,
                    created_at
                FROM models
                ORDER BY created_at DESC
                '''
            )

            models = [
                ShortModelInfo(
                    id=record['id'],
                    instrument_id=record['instrument_id'],
                    name=record['name'],
                    model_type=record['model_type'],
                    created_at=record['created_at']
                )
                for record in records
            ]

            return GetAllModelsInfo(models=models)

    @staticmethod
    def _get_model_class_by_type(model_type: str) -> Type[torch.nn.Module]:
        model_type = model_type.lower()
        match model_type:
            case 'lstm': return StockPriceLstm

        raise ValueError(f'Model type {model_type} not recognized')

    @staticmethod
    def _get_configuration_class_by_type(model_type: str) -> Type:
        model_type = model_type.lower()
        match model_type:
            case 'lstm': return LstmConfiguration

        raise ValueError(f'Model type {model_type} not recognized')

    @staticmethod
    def _load_dataclass(cls: Type[T], data: dict, **field_types) -> T:
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
                    converted[field.name] = PgModelRepository._load_dataclass(field.type, value)
                elif is_dataclass(field_types.get(field.name)):
                    converted[field.name] = PgModelRepository._load_dataclass(field_types.get(field.name), value)
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