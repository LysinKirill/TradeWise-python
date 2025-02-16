# import argparse
# import importlib
# import os
# import psycopg2
# from datetime import datetime
#
# from migrations.MigrationInfo import MigrationInfo
#
# conn = psycopg2.connect(
#     database="python-db",
#     user="postgres",
#     password="postgres",
#     host="localhost",
#     port=5432)
#
#
# MIGRATION_DIR = "migrations"
#
#
# def get_migration_classes() -> list[str]:
#     """Returns a list of all migration files"""
#     migrations = []
#     for file_name in os.listdir(MIGRATION_DIR):
#         if file_name.endswith(".py") and file_name != "__init__.py":
#             migration_name = file_name.replace(".py", "")
#             migrations.append(migration_name)
#     return migrations
#
#
# def apply_migration(migration_name, direction="up"):
#     """Applies or reverts a specific migration"""
#     module = importlib.import_module(f"{MIGRATION_DIR}.{migration_name}")
#     migration_class = getattr(module, migration_name)
#
#     # Call the appropriate migration method (up or down)
#     if direction == "up":
#         migration_class.up()
#     elif direction == "down":
#         migration_class.down()
#
#
# # def migrate_up(target_version):
# #     """Migrates up to the specified target version"""
# #     current_version = get_current_version()
# #     migrations = get_migrations()
# #
# #     for migration in migrations:
# #         migration_version = int(migration.split('_')[1])
# #         if int(current_version) < migration_version <= int(target_version):
# #             print(f"Applying {migration}...")
# #             apply_migration(migration, direction="up")
# #             set_current_version(migration_version)
# #         else:
# #             print(f"Migration {migration} already applied.")
# #
# #
# # def migrate_down(target_version):
# #     """Migrates down to the specified target version"""
# #     current_version = get_current_version()
# #     migrations = get_migrations()
# #
# #     for migration in migrations:
# #         migration_version = int(migration.split('_')[1])
# #         if migration_version > int(target_version):
# #             print(f"Reverting {migration}...")
# #             apply_migration(migration, direction="down")
# #             set_current_version(migration_version)
# #         else:
# #             print(f"Migration {migration} already reverted.")
#
#
# # def migrate(target_version):
# #     """Migrates to the specified version (up or down)"""
# #     current_version = get_current_version()
# #     if int(target_version) > int(current_version):
# #         print(f"Migrating up to version {target_version}...")
# #         migrate_up(target_version)
# #     elif int(target_version) < int(current_version):
# #         print(f"Migrating down to version {target_version}...")
# #         migrate_down(target_version)
# #     else:
# #         print(f"Already at version {target_version}. No migration needed.")
#
#
# # def migrate_latest():
# #     """Migrates to the latest available version"""
# #     current_version = get_current_version()
# #     migrations = get_migrations()
# #
# #     latest_version = max([int(m.split('_')[1]) for m in migrations])
# #
# #     if int(current_version) < latest_version:
# #         print(f"Migrating up to latest version {latest_version}...")
# #         migrate_up(latest_version)
# #     else:
# #         print("Already at the latest version.")
#
# def get_version_info() -> list[(int, str, datetime, str)]:
#     """Returns migrations version info from database"""
#     with conn.cursor() as cursor:
#         cursor.execute(
#             "SELECT id, version, appliedon, description FROM migration_version")
#         version_info: list[(int, str, datetime, str)] = cursor.fetchall()
#     return version_info
#
#
# def migrate() -> None:
#     """Migrates the database"""
#     migrations = get_migration_classes()
#     migration_ids = map(lambda x: x[0], migrations)
#     version_info = get_version_info()
#
#
#
#
# def create_version_table_if_not_exists() -> None:
#     """Creates the version table if it doesn't exist"""
#     with conn.cursor() as cursor:
#         cursor.execute(
#             '''CREATE TABLE IF NOT EXISTS versioninfo (
#                     id serial PRIMARY KEY,
#                     version integer,
#                     applied_on timestamp,
#                     descirption text);
#             ''')
#     conn.commit()
#
#
# def main():
#     create_version_table_if_not_exists()
#
#     parser = argparse.ArgumentParser(description="Manage database migrations.")
#
#     parser.add_argument("command", choices=["migrate", "up", "down"], help="Migration command")
#     parser.add_argument("version", nargs="?", help="Migration version (for migrate, up, and down)")
#
#     #args = parser.parse_args()
#
#     #if args.command == "migrate":
#     #    if args.version:
#     #        migrate(args.version)
#     #    else:
#     #        migrate_latest()
#     #elif args.command == "up":
#     #    if args.version:
#     #        migrate_up(args.version)
#     #    else:
#     #        print("Please provide a target version for migration.")
#     #elif args.command == "down":
#     #    if args.version:
#     #        migrate_down(args.version)
#     #    else:
#     #        print("Please provide a target version for migration.")
#
#
# if __name__ == "__main__":
#     main()







import argparse
import importlib
import os
from datetime import datetime
import os
import importlib.util
from pathlib import Path
import pydapper


from migrations.MigrationInfo import MigrationInfo


def get_version_info(commands) -> list[MigrationInfo]:
    """Returns migrations version info from database"""
    version_info = commands.query(
    '''
        select
            id, version, appliedon, description
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
    migrations_folder = Path(".")
    migration_classes = []

    for file in migrations_folder.glob("*.py"):
        if file.name == "__init__.py":
            continue

        module_name = file.stem
        spec = importlib.util.spec_from_file_location(module_name, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Iterate over all attributes in the module
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


def main() -> None:
    print("Loading migration classes...")
    migration_classes = load_migration_classes()
    print(f"A total of {len(migration_classes)} migration classes were loaded.")

    with (pydapper.connect(get_connection_string(
            user='postgres',
            password='postgres',
            host='localhost',
            port=5432,
            dbname='python-db')) as commands):
        create_version_table_if_not_exists(commands)
        db_version_info = get_version_info(commands)
        migrations_to_apply = sorted(
            filter(
                lambda migration_cls: should_apply_migration(db_version_info, migration_cls.version),
                migration_classes
            ),
            key=lambda migration_cls: migration_cls.version)

        for migration in migrations_to_apply:
            migration_obj = migration()
            migration_obj.migrate_up()
            print(f"Applied migration: Version {migration.version}, Description {migration.description}")

    print("Done.")


if __name__ == "__main__":
    main()