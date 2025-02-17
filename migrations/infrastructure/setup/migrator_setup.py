from pathlib import Path
import importlib.util
from datetime import datetime
from pydapper.commands import Commands
from migrations.MigrationInfo import MigrationInfo

def get_version_info(commands) -> list[MigrationInfo]:
    """Returns migrations version info from database"""
    version_info = commands.query(
        '''
            select
                id, version, applied_on, description
            from version_info
            order by version
            ''',
        model=MigrationInfo)
    return version_info

def create_version_table_if_not_exists(commands) -> None:
    """Creates the version table if it doesn't exist"""
    commands.execute(
        '''CREATE TABLE IF NOT EXISTS version_info (
                id serial PRIMARY KEY,
                version integer UNIQUE,
                applied_on timestamp,
                description text);
        ''')

def load_migration_classes():
    migrations_folder = Path("migrations")
    migration_classes = []

    for file in migrations_folder.glob("*.py"):
        if file.name == "__init__.py":
            continue

        module_name = file.stem
        spec = importlib.util.spec_from_file_location(module_name, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if isinstance(attr, type) and getattr(attr, "_is_migration", False):
                migration_classes.append(attr)

    return migration_classes

def get_connection_string(user: str, password: str, host: str, port: int, dbname: str) -> str:
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

def should_apply_migration(migration_info: list[MigrationInfo], migration_version: int) -> bool:
    return not any(
        [migration.version == migration_version and migration.applied_on is not None] for migration in migration_info)

def log_migrations_info(logger, migrations, annotation: str | None = None) -> None:
    """Log migration information using the logging library."""
    if annotation:
        logger.info(annotation)
    for migration in migrations:
        logger.info(f"Version: {migration.version}; Description: {migration.description}")

def save_applied_migration_in_db(commands: Commands, version: int, description: str, applied_on: datetime) -> None:
    commands.execute(
        sql='''
        insert into version_info (version, applied_on, description)
        values (?version?, ?applied_on?, ?description?);
        ''',
        param={"description": description, "applied_on": applied_on, "version": version},
    )