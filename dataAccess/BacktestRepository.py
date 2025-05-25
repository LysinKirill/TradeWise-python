from datetime import datetime
from pydapper.commands import CommandsAsync
from dataAccess.interfaces.IBacktestRepository import IBacktestRepository
from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider
from dataAccess.models.backtest.BacktestRecord import BacktestRecord
from dataAccess.models.backtest.BacktestStatus import BacktestStatus


class BacktestRepository(IBacktestRepository):
    def __init__(self, connection_provider: IPgConnectionProvider):
        self.connection_provider = connection_provider

    async def create_backtest(
            self,
            user_id: int,
            model_id: int,
            allocated_amount: float,
            from_: datetime,
            to: datetime
    ) -> int:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            backtest_id = await commands.execute_scalar_async(
                '''
                INSERT INTO backtests (
                    user_id,
                    model_id,
                    test_period_start,
                    test_period_end,
                    status,
                    initial_balance
                )
                VALUES
                (
                    ?user_id?,
                    ?model_id?,
                    ?test_period_start?,
                    ?test_period_end?,
                    ?status?,
                    ?initial_balance?
                )
                RETURNING id;
                ''',
                param={
                    "user_id": user_id,
                    "model_id": model_id,
                    "test_period_start": from_,
                    "test_period_end": to,
                    "status": BacktestStatus.PENDING.value,
                    "initial_balance": allocated_amount
                }
            )

            return backtest_id

    async def get_backtest(
            self,
            backtest_id: int
    ) -> BacktestRecord | None:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            backtest = await commands.query_first_or_default_async(
                '''
                SELECT
                    b.id,
                    b.started_at,
                    b.finished_at,
                    b.test_period_start,
                    b.test_period_end,
                    b.status,
                    b.profit,
                    b.trades_count,
                    b.initial_balance,
                    b.final_balance,
                    b.created_at,
                    u.id as user_id,
                    u.email,
                    u.invest_api_key,
                    u.invest_account_id,
                    m.id as model_id,
                    m.instrument_id,
                    m."name" as model_name,
                    m.type as model_type,
                    m.created_at as model_created_at
                FROM backtests b
                JOIN users u ON b.user_id = u.id
                JOIN models m ON b.model_id = m.id
                WHERE b.id = ?backtest_id?
                ''',
                param={"backtest_id": backtest_id},
                model=BacktestRecord,
                default=None
            )

            return backtest

    async def update_backtest_status(
            self,
            backtest_id: int,
            status: BacktestStatus,
            started_at: datetime | None = None,
            finished_at: datetime | None = None
    ) -> bool:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            updated = await commands.execute_async(
                '''
                UPDATE backtests
                SET
                    status = ?status?,
                    started_at = COALESCE(?started_at?, started_at),
                    finished_at = COALESCE(?finished_at?, finished_at)
                WHERE id = ?backtest_id?
                ''',
                param={
                    "status": status.value,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "backtest_id": backtest_id
                }
            )

            return updated > 0
