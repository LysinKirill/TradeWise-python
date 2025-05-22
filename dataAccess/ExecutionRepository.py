from datetime import datetime, timezone
from pydapper.commands import CommandsAsync
from dataAccess.interfaces.IExecutionRepository import IExecutionRepository, ExecutionRecord, ExecutionStatus
from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider
from dataAccess.models.common.ModelInfo import ModelInfo
from dataAccess.models.common.UserInfo import UserInfo


class ExecutionRepository(IExecutionRepository):
    def __init__(self, connection_provider: IPgConnectionProvider):
        self.connection_provider = connection_provider

    async def create_execution(
            self,
            user_email: str,
            model_id: int,
            allocated_amount: float,
            deadline: datetime | None = None
    ) -> int:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            execution_id_dict = await commands.query_first_or_default_async(
                '''
                WITH user_lookup AS (
                    SELECT id FROM users 
                    WHERE email = ?email?
                    LIMIT 1
                )
                INSERT INTO model_executions (
                    user_id,
                    model_id,
                    status,
                    deadline,
                    max_budget
                )
                SELECT 
                    ul.id,
                    ?model_id?,
                    ?status?,
                    ?deadline?,
                    ?budget?
                FROM user_lookup ul
                RETURNING id;
                ''',
                param={
                    "email": user_email,
                    "model_id": model_id,
                    "status": ExecutionStatus.PENDING.value,
                    "deadline": deadline,
                    "budget": allocated_amount,
                },
                default=None
            )

            if not (execution_id := execution_id_dict['id']):
                raise ValueError(f"Failed to create execution - user with email {user_email} not found")

            return execution_id

    async def get_execution(self, execution_id: int) -> ExecutionRecord | None:
        async with self.connection_provider.get_connection() as commands:
            commands: CommandsAsync

            record = await commands.query_first_or_default_async(
                '''
                SELECT
                    e.id,
                    e.status,
                    e.started_at,
                    e.finished_at,
                    e.deadline,
                    e.max_budget,
                    e.current_spent,
                    e.shares_owned,
                    u.id as user_id,
                    u.email,
                    u.invest_api_key,
                    u.invest_account_id,
                    m.id as model_id,
                    m.instrument_id,
                    m.name,
                    m.type,
                    m.created_at as model_created_at
                FROM model_executions e
                JOIN users u ON e.user_id = u.id
                JOIN models m ON e.model_id = m.id
                WHERE e.id = ?execution_id?
                ''',
                param={"execution_id": execution_id},
                default=None
            )

            if not record:
                return None

            return ExecutionRepository._parse_execution_record(record)

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
                    e.id,
                    e.status,
                    e.started_at,
                    e.finished_at,
                    e.deadline,
                    e.max_budget,
                    e.current_spent,
                    e.shares_owned,
                    u.id as user_id,
                    u.email,
                    u.invest_api_key,
                    u.invest_account_id,
                    m.id as model_id,
                    m.instrument_id,
                    m.name,
                    m.type,
                    m.created_at as model_created_at
                FROM model_executions e
                JOIN users u ON e.user_id = u.id
                JOIN models m ON e.model_id = m.id
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

            return list(map(ExecutionRepository._parse_execution_record, records))

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

    async def update_execution_financials(
            self,
            execution_id: int,
            current_spent_increment: float,
            shares_owned_increment: int
    ) -> bool:
        async with self.connection_provider.get_connection() as commands:
            updated = await commands.execute_async(
                '''
                UPDATE model_executions
                SET 
                    current_spent = current_spent + ?current_spent_increment?,
                    shares_owned = shares_owned + ?shares_owned_increment?
                WHERE id = ?execution_id?
                ''',
                param={
                    "current_spent_increment": current_spent_increment,
                    "shares_owned_increment": shares_owned_increment,
                    "execution_id": execution_id
                }
            )
            return updated > 0

    @staticmethod
    def _parse_execution_record(record: dict) -> ExecutionRecord:
        return ExecutionRecord(
            id=record['id'],
            status=ExecutionStatus(record['status']),
            started_at=record['started_at'],
            finished_at=record['finished_at'],
            deadline=record['deadline'],
            max_budget=record['max_budget'],
            current_spent=record['current_spent'],
            shares_owned=record['shares_owned'],
            user_info=UserInfo(
                id=record['user_id'],
                email=record['email'],
                invest_api_key=record['invest_api_key'],
                invest_account_id=record['invest_account_id']
            ),
            model_info=ModelInfo(
                id=record['model_id'],
                instrument_id=record['instrument_id'],
                name=record['name'],
                type=record['type'],
                created_at=record['model_created_at']
            )
        )