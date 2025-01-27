import os
import sys
import importlib
import argparse

# Path where migration files are located
MIGRATION_DIR = "migrations"

# Migration version file
VERSION_FILE = "db/migration_version.txt"


def get_current_version():
    """Reads the current version from the migration_version.txt file"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return "0"  # If no version file exists, assume version 0


def set_current_version(version):
    """Updates the version in the migration_version.txt file"""
    with open(VERSION_FILE, "w") as f:
        f.write(str(version))


def get_migrations():
    """Returns a list of all migration files"""
    migrations = []
    for file_name in os.listdir(MIGRATION_DIR):
        if file_name.endswith(".py") and file_name != "__init__.py":
            migration_name = file_name.replace(".py", "")
            migrations.append(migration_name)
    return migrations


def apply_migration(migration_name, direction="up"):
    """Applies or reverts a specific migration"""
    module = importlib.import_module(f"{MIGRATION_DIR}.{migration_name}")
    migration_class = getattr(module, migration_name)

    # Call the appropriate migration method (up or down)
    if direction == "up":
        migration_class.up()
    elif direction == "down":
        migration_class.down()


def migrate_up(target_version):
    """Migrates up to the specified target version"""
    current_version = get_current_version()
    migrations = get_migrations()

    for migration in migrations:
        migration_version = int(migration.split('_')[1])
        if int(current_version) < migration_version <= int(target_version):
            print(f"Applying {migration}...")
            apply_migration(migration, direction="up")
            set_current_version(migration_version)
        else:
            print(f"Migration {migration} already applied.")


def migrate_down(target_version):
    """Migrates down to the specified target version"""
    current_version = get_current_version()
    migrations = get_migrations()

    for migration in migrations:
        migration_version = int(migration.split('_')[1])
        if migration_version > int(target_version):
            print(f"Reverting {migration}...")
            apply_migration(migration, direction="down")
            set_current_version(migration_version)
        else:
            print(f"Migration {migration} already reverted.")


def migrate(target_version):
    """Migrates to the specified version (up or down)"""
    current_version = get_current_version()
    if int(target_version) > int(current_version):
        print(f"Migrating up to version {target_version}...")
        migrate_up(target_version)
    elif int(target_version) < int(current_version):
        print(f"Migrating down to version {target_version}...")
        migrate_down(target_version)
    else:
        print(f"Already at version {target_version}. No migration needed.")


def migrate_latest():
    """Migrates to the latest available version"""
    current_version = get_current_version()
    migrations = get_migrations()

    latest_version = max([int(m.split('_')[1]) for m in migrations])

    if int(current_version) < latest_version:
        print(f"Migrating up to latest version {latest_version}...")
        migrate_up(latest_version)
    else:
        print("Already at the latest version.")


def main():
    parser = argparse.ArgumentParser(description="Manage database migrations.")

    parser.add_argument("command", choices=["migrate", "up", "down"], help="Migration command")
    parser.add_argument("version", nargs="?", help="Migration version (for migrate, up, and down)")

    args = parser.parse_args()

    if args.command == "migrate":
        if args.version:
            migrate(args.version)
        else:
            migrate_latest()
    elif args.command == "up":
        if args.version:
            migrate_up(args.version)
        else:
            print("Please provide a target version for migration.")
    elif args.command == "down":
        if args.version:
            migrate_down(args.version)
        else:
            print("Please provide a target version for migration.")


if __name__ == "__main__":
    main()
