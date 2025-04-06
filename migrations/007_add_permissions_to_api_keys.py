import peewee as pw
from playhouse.migrate import SchemaMigrator
from peewee_migrate import Migrator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    migrator = SchemaMigrator.from_database(database)

    with database.atomic():
        try:
            # Check if the column already exists
            logger.info("Checking if 'permissions' column exists...")
            existing_columns = database.get_columns('apikey')
            if 'permissions' not in [col.name for col in existing_columns]:
                logger.info("Adding the 'permissions' column with a default value of an empty string...")
                database.execute_sql('ALTER TABLE apikey ADD COLUMN permissions TEXT DEFAULT "";')
                logger.info("Migration completed successfully.")
            else:
                logger.info("'permissions' column already exists. Skipping migration.")
        except Exception as e:
            logger.error(f"An error occurred during migration: {e}")
            raise

def rollback(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    with database.atomic():
        try:
            # Check if the column exists before dropping it
            logger.info("Checking if 'permissions' column exists...")
            existing_columns = database.get_columns('apikey')
            if 'permissions' in [col.name for col in existing_columns]:
                logger.info("Removing the 'permissions' column...")
                database.execute_sql('ALTER TABLE apikey DROP COLUMN permissions;')
                logger.info("Rollback completed successfully.")
            else:
                logger.info("'permissions' column does not exist. Skipping rollback.")
        except Exception as e:
            logger.error(f"An error occurred during rollback: {e}")
            raise