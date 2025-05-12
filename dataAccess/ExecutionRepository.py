from datetime import datetime, timezone
from pydapper.commands import CommandsAsync
from dataAccess.interfaces.IExecutionRepository import IExecutionRepository, ExecutionRecord, ExecutionStatus
from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider


class ExecutionRepository(IExecutionRepository):
    def __init__(self, connection_provider: IPgConnectionProvider):
        self.connection_provider = connection_provider

    async def create_execution(
        self,
        user_id: int,
        model_id: int,
        deadline: datetime | None = None
    ) -> ExecutionRecord:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            execution_id = await commands.execute_scalar_async(
                '''
                INSERT INTO model_executions (
                    user_id,
                    model_id,
                    status,
                    deadline
                )
                VALUES (
                    ?user_id?,
                    ?model_id?,
                    ?status?,
                    ?deadline?
                )
                RETURNING id;
                ''',
                param={
                    "user_id": user_id,
                    "model_id": model_id,
                    "status": ExecutionStatus.PENDING.value,
                    "deadline": deadline
                }
            )

            return ExecutionRecord(
                id=execution_id,
                user_id=user_id,
                model_id=model_id,
                status=ExecutionStatus.PENDING,
                started_at=None,
                finished_at=None,
                deadline=deadline
            )

    async def get_execution(self, execution_id: int) -> ExecutionRecord | None:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            record = await commands.query_first_async(
                '''
                SELECT
                    id,
                    user_id,
                    model_id,
                    status,
                    started_at,
                    finished_at,
                    deadline
                FROM model_executions
                WHERE id = ?execution_id?
                ''',
                param={"execution_id": execution_id}
            )

            if not record:
                return None

            return ExecutionRecord(
                id=record['id'],
                user_id=record['user_id'],
                model_id=record['model_id'],
                status=ExecutionStatus(record['status']),
                started_at=record['started_at'],
                finished_at=record['finished_at'],
                deadline=record['deadline']
            )

    async def get_executions_by_status(
        self,
        statuses: list[ExecutionStatus]
    ) -> list[ExecutionRecord]:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            status_values = [status.value for status in statuses]
            records = await commands.query_async(
                '''
                SELECT
                    id,
                    user_id,
                    model_id,
                    status,
                    started_at,
                    finished_at,
                    deadline
                FROM model_executions
                WHERE status = ANY(?statuses?)
                ORDER BY 
                    CASE 
                        WHEN deadline IS NULL THEN 1
                        ELSE 0
                    END,
                    deadline ASC
                ''',
                param={"statuses": status_values}
            )

            return [
                ExecutionRecord(
                    id=record['id'],
                    user_id=record['user_id'],
                    model_id=record['model_id'],
                    status=ExecutionStatus(record['status']),
                    started_at=record['started_at'],
                    finished_at=record['finished_at'],
                    deadline=record['deadline']
                )
                for record in records
            ]

    async def update_execution_status(
        self,
        execution_id: int,
        status: ExecutionStatus,
        started_at: datetime | None = None,
        finished_at: datetime | None = None
    ) -> bool:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            updated = await commands.execute_async(
                '''
                UPDATE model_executions
                SET
                    status = ?status?,
                    started_at = COALESCE(?started_at?, started_at),
                    finished_at = COALESCE(?finished_at?, finished_at)
                WHERE id = ?execution_id?
                ''',
                param={
                    "status": status.value,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "execution_id": execution_id
                }
            )

            return updated > 0

    async def set_execution_deadline(
        self,
        execution_id: int,
        deadline: datetime
    ) -> bool:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            updated = await commands.execute_async(
                '''
                UPDATE model_executions
                SET deadline = ?deadline?
                WHERE id = ?execution_id?
                ''',
                param={
                    "deadline": deadline,
                    "execution_id": execution_id
                }
            )

            return updated > 0

    async def cleanup_expired_executions(self) -> int:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            now = datetime.now(timezone.utc)
            updated = await commands.execute_async(
                '''
                UPDATE model_executions
                SET status = ?failed_status?
                WHERE status IN (?pending_status?, ?running_status?)
                AND deadline IS NOT NULL
                AND deadline < ?now?
                ''',
                param={
                    "failed_status": ExecutionStatus.FAILED.value,
                    "pending_status": ExecutionStatus.PENDING.value,
                    "running_status": ExecutionStatus.RUNNING.value,
                    "now": now
                }
            )

            return updated