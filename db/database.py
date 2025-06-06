import aiosqlite

DB_PATH = "yuuki_bot.db"

async def initialize():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel INTEGER,
                rules_channel INTEGER,
                heartbeat_channel INTEGER,
                role_channel INTEGER,
                introduction_channel INTEGER,
                goodbye_channel INTEGER,
                list_channel INTEGER,
                log_channel INTEGER
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS autoroles (
                guild_id INTEGER,
                role_id INTEGER
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS infractions (
                guild_id INTEGER,
                user_id INTEGER,
                mod_id INTEGER,
                action TEXT,
                reason TEXT,
                timestamp INTEGER
            );
        """)
        await db.commit()

async def ensure_guild_exists(bot, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
        await db.commit()

async def set_channel_id(bot, guild_id, column, channel_id):
    await ensure_guild_exists(bot, guild_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE guild_settings SET {column} = ? WHERE guild_id = ?", (channel_id, guild_id))
        await db.commit()

async def get_channel_id(bot, guild_id, column):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(f"SELECT {column} FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def remove_channel_id(bot, guild_id, column):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE guild_settings SET {column} = NULL WHERE guild_id = ?", (guild_id,))
        await db.commit()

async def add_autorole(bot, guild_id, role_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO autoroles (guild_id, role_id) VALUES (?, ?)", (guild_id, role_id))
        await db.commit()

async def remove_autorole(bot, guild_id, role_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM autoroles WHERE guild_id = ? AND role_id = ?", (guild_id, role_id))
        await db.commit()

async def get_autoroles(bot, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT role_id FROM autoroles WHERE guild_id = ?", (guild_id,)) as cursor:
            return [row[0] for row in await cursor.fetchall()]

async def log_infraction(bot, guild_id, user_id, mod_id, action, reason, timestamp):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO infractions (guild_id, user_id, mod_id, action, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guild_id, user_id, mod_id, action, reason, timestamp))
        await db.commit()

async def get_infractions(bot, guild_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT mod_id, action, reason, timestamp
            FROM infractions
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id)) as cursor:
            return [{"mod_id": row[0], "action": row[1], "reason": row[2], "timestamp": row[3]} for row in await cursor.fetchall()]
