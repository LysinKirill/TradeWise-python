import io
import json
import torch
import copy
from pydapper.commands import CommandsAsync
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider
from dataAccess.models.model.GetAllModelsInfo import GetAllModelsInfo
from dataAccess.models.model.GetModelResponse import GetModelResponse
from typing import Any

from dataAccess.models.model.ShortModelInfo import ShortModelInfo


class PgModelRepository(IModelRepository):
    def __init__(self, connection_provider: IPgConnectionProvider):
        self.connection_provider = connection_provider

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
            model_for_init: torch.nn.Module
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