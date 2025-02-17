from .ForwardMigration import ForwardMigration
from .InvalidMigrationException import InvalidMigrationException

def migration(version: int, description: str = None):
    if description is None:
        description = f'Database migration of version {version}'
    def wrapper(cls):
        if not (issubclass(cls, ForwardMigration)):
            raise InvalidMigrationException(
                "Class marked with migration attribute should inherit from ForwardMigration class")
        cls._is_migration = True
        cls.description = description
        cls.version = version
        return cls
    return wrapper