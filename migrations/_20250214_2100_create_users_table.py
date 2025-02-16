from pydapper.commands import Commands

from infrastructure.MigrationAttribute import *


@migration(version=1, description="Create users table (id, email, invest_api_key)")
class _20025014_2100_create_users_table(ForwardMigration):
    def migrate_up(self, commands: Commands) -> None:
        commands.execute(
            sql='''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                invest_api_key TEXT
            );
            '''
        )
