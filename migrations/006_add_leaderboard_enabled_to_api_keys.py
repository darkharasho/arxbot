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
            # Step 1: Add the 'leaderboard_enabled' column with a default value of True
            print("Adding the 'leaderboard_enabled' column with a default value of True...")
            database.execute_sql('ALTER TABLE apikey ADD COLUMN leaderboard_enabled BOOLEAN DEFAULT TRUE;')

            print("Migration completed successfully.")

        except Exception as e:
            print(f"An error occurred during migration: {e}")
            raise

def rollback(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    with database.atomic():
        try:
            # Step 1: Remove the 'leaderboard_enabled' column
            print("Removing the 'leaderboard_enabled' column...")
            database.execute_sql('ALTER TABLE apikey DROP COLUMN leaderboard_enabled;')

            print("Rollback completed successfully.")

        except Exception as e:
            print(f"An error occurred during rollback: {e}")
            raise

# Final log to confirm script completion
print("Migration script execution completed.")
