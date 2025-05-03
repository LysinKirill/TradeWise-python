from pydapper.commands import CommandsAsync

from migrations.infrastructure.MigrationAttribute import *


@migration(version=2, description="Create models table (id, email, invest_api_key)")
class _20250503_0300_create_models_table(ForwardMigration):
    async def migrate_up(self, commands: CommandsAsync) -> None:
        await commands.execute_async(
            sql='''
            CREATE TABLE IF NOT EXISTS models (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_bytes BYTEA NOT NULL,
                norm_min FLOAT NOT NULL,
                norm_max FLOAT NOT NULL
            );
            '''
        )
