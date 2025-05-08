import pydapper

from contextlib import asynccontextmanager
from pydapper.commands import CommandsAsync
from dataAccess.interfaces.IPgConnectionProvider import IPgConnectionProvider
from typing import AsyncIterator


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


    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[CommandsAsync]:
        async with pydapper.connect_async(
            PgConnectionProvider._get_connection_string(
                user=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                dbname=self.db
            )
        ) as connection:
            yield connection

    @staticmethod
    def _get_connection_string(user: str, password: str, host: str, port: int, dbname: str) -> str:
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
