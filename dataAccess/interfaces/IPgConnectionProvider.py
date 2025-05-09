from pydapper.commands import CommandsAsync
from typing import AsyncIterator
from abc import ABC, abstractmethod


class IPgConnectionProvider(ABC):
    @abstractmethod
    async def get_connection(self) -> AsyncIterator[CommandsAsync]:
        pass