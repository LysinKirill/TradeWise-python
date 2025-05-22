from pydapper.commands import CommandsAsync
from migrations.infrastructure.MigrationAttribute import *


@migration(version=2, description="Create models table with type and config columns")
class _20250503_0300_create_models_table(ForwardMigration):
    async def migrate_up(self, commands: CommandsAsync) -> None:
        await commands.execute_async(
            sql='''
            CREATE TABLE IF NOT EXISTS models (
                id SERIAL PRIMARY KEY,
                instrument_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_bytes BYTEA NOT NULL,
                config JSONB NOT NULL
            );
            '''
        )