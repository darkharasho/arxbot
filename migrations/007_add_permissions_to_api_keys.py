import peewee as pw
from playhouse.migrate import SchemaMigrator
from peewee_migrate import Migrator

# Initial log to confirm script execution
print("Starting migration script...")

def migrate(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    # Get the current migrator for the database
    migrator = SchemaMigrator.from_database(database)

    with database.atomic():
        try:
            # Step 1: Add the 'permissions' column with a default value of an empty string
            print("Adding the 'permissions' column with a default value of an empty string...")
            database.execute_sql('ALTER TABLE apikey ADD COLUMN permissions TEXT DEFAULT "";')

            print("Migration completed successfully.")

        except Exception as e:
            print(f"An error occurred during migration: {e}")
            raise

def rollback(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    with database.atomic():
        try:
            # Step 1: Remove the 'permissions' column
            print("Removing the 'permissions' column...")
            database.execute_sql('ALTER TABLE apikey DROP COLUMN permissions;')

            print("Rollback completed successfully.")

        except Exception as e:
            print(f"An error occurred during rollback: {e}")
            raise

# Final log to confirm script completion
print("Migration script execution completed.")