from pydapper.commands import CommandsAsync
from migrations.infrastructure.MigrationAttribute import *


@migration(version=3, description="Create model executions table with financial tracking")
class _20250510_2000_create_executions_table(ForwardMigration):
    async def migrate_up(self, commands: CommandsAsync) -> None:
        await commands.execute_async(
            sql='''
            CREATE TABLE IF NOT EXISTS model_executions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                model_id INTEGER NOT NULL REFERENCES models(id),
                status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
                started_at TIMESTAMP WITH TIME ZONE,
                finished_at TIMESTAMP WITH TIME ZONE,
                deadline TIMESTAMP WITH TIME ZONE,
                max_budget NUMERIC(20, 2) NOT NULL,
                current_spent NUMERIC(20, 2) DEFAULT 0.00,
                shares_owned INTEGER DEFAULT 0
            );
            '''
        )