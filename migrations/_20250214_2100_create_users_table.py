from pydapper.commands import CommandsAsync
from migrations.infrastructure.MigrationAttribute import *


@migration(version=1, description="Create users table (id, email, invest_api_key)")
class _20025014_2100_create_users_table(ForwardMigration):
    async def migrate_up(self, commands: CommandsAsync) -> None:
        await commands.execute_async(
            sql='''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                invest_api_key TEXT
            );
            '''
        )
