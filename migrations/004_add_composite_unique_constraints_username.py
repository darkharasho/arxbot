import peewee as pw
from playhouse.migrate import SchemaMigrator
from peewee_migrate import Migrator

def migrate(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    # Get the current migrator for SQLite
    migrator = SchemaMigrator.from_database(database)

    with database.atomic():
        # Step 1: Rename the existing table
        database.execute_sql('ALTER TABLE member RENAME TO member_old;')

        # Step 2: Create a new member table without unique constraints
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

        # Step 3: Remove duplicates from the old table (if any)
        duplicates = database.execute_sql('''
        SELECT MIN(id) as id, guild_id, discord_id, username 
        FROM member_old 
        GROUP BY guild_id, discord_id, username 
        HAVING COUNT(*) > 1;
        ''')

        for duplicate in duplicates.fetchall():
            id, guild_id, discord_id, username = duplicate
            # Keep one record and remove others
            database.execute_sql('''
            DELETE FROM member_old 
            WHERE guild_id = ? AND discord_id = ? AND username = ? AND id != ?;
            ''', (guild_id, discord_id, username, id))

        # Step 4: Copy data from the old table to the new table
        database.execute_sql('''
        INSERT INTO member (id, username, guild_id, discord_id, user_id, gw2_api_key, gw2_stats, gw2_username, created_at, updated_at)
        SELECT id, username, guild_id, discord_id, user_id, gw2_api_key, gw2_stats, gw2_username, created_at, updated_at
        FROM member_old;
        ''')

        # Step 5: Drop existing indexes if they exist
        database.execute_sql('DROP INDEX IF EXISTS member_guild_id_discord_id;')
        database.execute_sql('DROP INDEX IF EXISTS member_guild_id_username;')

        # Step 6: Add the composite unique indexes
        database.execute_sql('''
        CREATE UNIQUE INDEX member_guild_id_discord_id ON member (guild_id, discord_id);
        ''')
        database.execute_sql('''
        CREATE UNIQUE INDEX member_guild_id_username ON member (guild_id, username);
        ''')

        # Step 7: Drop the old table
        database.execute_sql('DROP TABLE member_old;')

def rollback(migrator: Migrator, database: pw.Database, fake=False, **kwargs):
    # Implement rollback logic if necessary
    pass
