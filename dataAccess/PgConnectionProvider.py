import pydapper

from pydapper.commands import Commands
from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider


class PgConnectionProvider(IPgConnectionProvider):
    def __init__(
            self,
            username: str,
            password: str,
            host: str,
            port: int,
            db: str,
    ):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.db = db

    def get_connection(self) -> Commands:
        return pydapper.connect(PgConnectionProvider._get_connection_string(
            user=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            dbname=self.db))

    @staticmethod
    def _get_connection_string(user: str, password: str, host: str, port: int, dbname: str) -> str:
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
