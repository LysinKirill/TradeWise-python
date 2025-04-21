from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider
from dataAccess.interfaces.IUserRepository import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, connection_provider: IPgConnectionProvider):
        self.connection_provider = connection_provider

    async def add_invest_api_key(self, email: str, api_key: str) -> bool:
        async with (self.connection_provider.get_connection() as commands):
            add_key_success = await commands.execute(
                '''
                INSERT INTO "users" (email, invest_api_key)
                VALUES (?email?, ?invest_api_key?)
                ON CONFLICT (email) 
                DO UPDATE SET  invest_api_key = ?invest_api_key?;
                ''',
                param={"invest_api_key": api_key, "email": email})
            return add_key_success
