from abc import ABC, abstractmethod


class ForwardMigration(ABC):
    @abstractmethod
    def migrate_up(self):
        pass