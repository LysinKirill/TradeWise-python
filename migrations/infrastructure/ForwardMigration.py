import pydapper
from abc import ABC, abstractmethod

from pydapper.commands import Commands


class ForwardMigration(ABC):
    @abstractmethod
    def migrate_up(self, commands: Commands) -> None:
        pass