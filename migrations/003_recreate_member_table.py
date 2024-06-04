import peewee as pw
from playhouse.migrate import SchemaMigrator
from peewee_migrate import Migrator

def migrate(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    # Get the current migrator for SQLite
    migrator = SchemaMigrator.from_database(database)

    with database.atomic():
        # Step 1: Rename the existing table
        database.execute_sql('ALTER TABLE member RENAME TO member_old;')

        # Step 2: Create a new member table without unique constraint on discord_id
        database.execute_sql('''
        CREATE TABLE member (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
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

        # Step 3: Copy data from the old table to the new table
        database.execute_sql('''
        INSERT INTO member (id, username, guild_id, discord_id, user_id, gw2_api_key, gw2_stats, gw2_username, created_at, updated_at)
        SELECT id, username, guild_id, discord_id, user_id, gw2_api_key, gw2_stats, gw2_username, created_at, updated_at
        FROM member_old;
        ''')

        # Step 4: Drop the composite unique index if it exists
        try:
            database.execute_sql('DROP INDEX IF EXISTS member_guild_id_discord_id;')
        except pw.OperationalError:
            pass

        # Step 5: Add the composite unique index
        database.execute_sql('''
        CREATE UNIQUE INDEX member_guild_id_discord_id ON member (guild_id, discord_id);
        ''')

        # Step 6: Drop the old table
        database.execute_sql('DROP TABLE member_old;')

def rollback(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    # Implement rollback logic if necessary
    pass
