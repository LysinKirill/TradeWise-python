import pydapper
from abc import ABC, abstractmethod

from pydapper.commands import Commands


class ForwardMigration(ABC):
    @abstractmethod
    async def migrate_up(self, commands: Commands) -> None:
        pass