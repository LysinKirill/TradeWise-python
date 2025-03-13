from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider
from dataAccess.interfaces.IUserRepository import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, connection_provider: IPgConnectionProvider):
        self.connection_provider = connection_provider

    def add_invest_api_key(self, email: str, api_key: str) -> bool:
        with (self.connection_provider.get_connection() as commands):
            add_key_success = commands.query_single(
                '''
                    update "users" u
                    set invest_api_key = ?invest_api_key?
                    where u.email = ?email?
                    returning true;
                ''',
                param={"invest_api_key": api_key, "email": email})
            return add_key_success
