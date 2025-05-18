from pydapper.commands import CommandsAsync
from migrations.infrastructure.MigrationAttribute import *


@migration(version=4, description="Add invest_account_id to users table")
class _20250510_2300_add_invest_account_id_to_users(ForwardMigration):
    async def migrate_up(self, commands: CommandsAsync) -> None:
        await commands.execute_async(
            sql='''
            ALTER TABLE users
            ADD COLUMN invest_account_id TEXT NULL;
            '''
        )