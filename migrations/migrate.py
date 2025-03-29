import pydapper
from datetime import datetime
from migrations.infrastructure.setup.logger_setup import setup_logging
from migrations.infrastructure.setup.migrator_setup import (
    get_version_info,
    create_version_table_if_not_exists,
    load_migration_classes,
    get_connection_string,
    should_apply_migration,
    log_migrations_info,
    save_applied_migration_in_db,
)


logger = setup_logging()

def main() -> None:
    logger.info("Loading migration classes...")
    migration_classes = load_migration_classes()
    logger.info(f"A total of {len(migration_classes)} migration classes were loaded.")

    with (pydapper.connect(get_connection_string(
            user='postgres',
            password='postgres',
            host='localhost',
            port=5433,
            dbname='python-db')) as commands):
        create_version_table_if_not_exists(commands)
        db_version_info = get_version_info(commands)

        skipped_migrations = []
        failed_migrations = []
        applied_migrations = []

        current_datetime = datetime.now()

        for migration_cls in migration_classes:
            try:
                if should_apply_migration(db_version_info, migration_cls.version):
                    migration_obj = migration_cls()
                    migration_obj.migrate_up(commands)
                    save_applied_migration_in_db(commands, migration_cls.version, migration_cls.description, current_datetime)
                    applied_migrations.append(migration_cls)
                    continue
                skipped_migrations.append(migration_cls)
            except Exception as e:
                logger.error(f"Error applying migration {migration_cls.__name__}: {e}")
                failed_migrations.append(migration_cls)

        log_migrations_info(logger, skipped_migrations, "[SKIPPED MIGRATIONS]")
        if failed_migrations:
            log_migrations_info(logger, failed_migrations, "[FAILED MIGRATIONS]")
        log_migrations_info(logger, applied_migrations, "[APPLIED MIGRATIONS]")

    logger.info("Done.")

if __name__ == "__main__":
    main()