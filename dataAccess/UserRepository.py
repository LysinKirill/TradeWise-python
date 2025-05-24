from pydapper.commands import CommandsAsync

from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider
from dataAccess.interfaces.IUserRepository import IUserRepository
from dataAccess.models.common.UserInfo import UserInfo


class UserRepository(IUserRepository):
    def __init__(self, connection_provider: IPgConnectionProvider):
        self.connection_provider = connection_provider

    async def add_invest_api_key(self, email: str, api_key: str, invest_account_id: str) -> bool:
        async with (self.connection_provider.get_connection() as commands):
            commands: CommandsAsync
            add_key_success = await commands.execute_async(
                '''
                INSERT INTO "users" (email, invest_api_key, invest_account_id)
                VALUES (?email?, ?invest_api_key?, ?invest_account_id?)
                ON CONFLICT (email) 
                DO UPDATE SET  invest_api_key = ?invest_api_key?, invest_account_id = ?invest_account_id?;
                ''',
                param={"invest_api_key": api_key, "email": email, "invest_account_id":invest_account_id})
            return add_key_success > 0

    async def get_user_by_email(self, email: str) -> UserInfo | None:
        async with (self.connection_provider.get_connection() as commands):
            commands: CommandsAsync
            return await commands.query_first_or_default_async(
                '''
                SELECT 
                    u.id,
                    u.email,
                    u.invest_api_key,
                    u.invest_account_id
                FROM users u
                WHERE u.email = ?email?
                ''',
                param={"email": email},
                default=None
            )
