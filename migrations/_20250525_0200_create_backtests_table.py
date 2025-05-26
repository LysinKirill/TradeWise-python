from pydapper.commands import CommandsAsync
from migrations.infrastructure.MigrationAttribute import *


@migration(version=5, description="Create backtest executions table")
class _20250525_0200_create_backtests_table(ForwardMigration):
    async def migrate_up(self, commands: CommandsAsync) -> None:
        await commands.execute_async(
            sql='''
            CREATE TABLE IF NOT EXISTS backtests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                model_id INTEGER NOT NULL REFERENCES models(id),
                started_at TIMESTAMP WITH TIME ZONE,
                finished_at TIMESTAMP WITH TIME ZONE,
                test_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                test_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                profit NUMERIC(20, 2) NOT NULL DEFAULT 0,
                trades_count INTEGER NOT NULL DEFAULT 0,
                initial_balance NUMERIC(20, 2) NOT NULL,
                final_balance NUMERIC(20, 2),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            '''
        )