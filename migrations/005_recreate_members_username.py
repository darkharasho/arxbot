import peewee as pw
from playhouse.migrate import SchemaMigrator
from peewee_migrate import Migrator

# Initial log to confirm script execution
print("Starting migration script...")

def migrate(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    # Get the current migrator for SQLite
    migrator = SchemaMigrator.from_database(database)

    with database.atomic():
        try:
            # Step 1: Rename the existing table
            print("Renaming the existing member table to member_old...")
            database.execute_sql('ALTER TABLE member RENAME TO member_old;')

            # Step 2: Create a new member table without unique constraints
            print("Creating a new member table without unique constraints...")
            database.execute_sql('''
            CREATE TABLE member (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                guild_id INTEGER NOT NULL REFERENCES guild (id),
                discord_id INTEGER NOT NULL,
                user_id INTEGER,
                gw2_api_key TEXT,
                gw2_stats TEXT,
                gw2_username TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP,
                FOREIGN KEY (guild_id) REFERENCES guild (id)
            );
            ''')

            # Step 3: Identify and handle duplicates based on (guild_id, discord_id)
            print("Identifying and handling duplicates based on (guild_id, discord_id)...")
            duplicates = database.execute_sql('''
            SELECT id
            FROM (
                SELECT id, ROW_NUMBER() OVER(PARTITION BY guild_id, discord_id ORDER BY id) AS row_num
                FROM member_old
            )
            WHERE row_num > 1;
            ''').fetchall()
            duplicate_ids = [row[0] for row in duplicates]
            if duplicate_ids:
                print(f"Deleting duplicates based on (guild_id, discord_id): {duplicate_ids}")
                database.execute_sql('DELETE FROM member_old WHERE id IN (%s);' % ','.join(map(str, duplicate_ids)))

            # Identify and handle duplicates based on (guild_id, username)
            print("Identifying and handling duplicates based on (guild_id, username)...")
            duplicates = database.execute_sql('''
            SELECT id
            FROM (
                SELECT id, ROW_NUMBER() OVER(PARTITION BY guild_id, username ORDER BY id) AS row_num
                FROM member_old
            )
            WHERE row_num > 1;
            ''').fetchall()
            duplicate_ids = [row[0] for row in duplicates]
            if duplicate_ids:
                print(f"Deleting duplicates based on (guild_id, username): {duplicate_ids}")
                database.execute_sql('DELETE FROM member_old WHERE id IN (%s);' % ','.join(map(str, duplicate_ids)))

            # Step 4: Copy data from the old table to the new table
            print("Copying data from the old table to the new table...")
            database.execute_sql('''
            INSERT INTO member (id, username, guild_id, discord_id, user_id, gw2_api_key, gw2_stats, gw2_username, created_at, updated_at)
            SELECT id, username, guild_id, discord_id, user_id, gw2_api_key, gw2_stats, gw2_username, created_at, updated_at
            FROM member_old;
            ''')

            # Step 5: Drop the old table
            print("Dropping the old member_old table...")
            database.execute_sql('DROP TABLE member_old;')

            # Step 6: Add the composite unique indexes
            print("Adding composite unique indexes...")
            database.execute_sql('''
            CREATE UNIQUE INDEX member_guild_id_discord_id ON member (guild_id, discord_id);
            ''')
            database.execute_sql('''
            CREATE UNIQUE INDEX member_guild_id_username ON member (guild_id, username);
            ''')

            print("Migration completed successfully.")

        except Exception as e:
            print(f"An error occurred during migration: {e}")
            raise

def rollback(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    # Implement rollback logic if necessary
    pass

# Final log to confirm script completion
print("Migration script execution completed.")
