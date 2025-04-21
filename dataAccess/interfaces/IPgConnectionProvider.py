from abc import ABC, abstractmethod

from pydapper.commands import Commands


class IPgConnectionProvider(ABC):
    @abstractmethod
    async def get_connection(self) -> Commands:
        pass