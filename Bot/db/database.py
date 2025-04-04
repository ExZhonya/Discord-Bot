import asyncpg
import asyncio

async def init_db(bot):
    from dotenv import load_dotenv
    import os
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')

    bot.db = await asyncpg.connect(DATABASE_URL)

    # Auto create channels table
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            guild_id BIGINT PRIMARY KEY,
            welcome_channel BIGINT DEFAULT NULL,
            rules_channel BIGINT DEFAULT NULL,
            heartbeat_channel BIGINT DEFAULT NULL,
            role_channel BIGINT DEFAULT NULL,
            introduction_channel BIGINT DEFAULT NULL
        )
    """)

    await bot.db.execute("""
    CREATE TABLE IF NOT EXISTS autoroles (
        guild_id BIGINT,
        role_id BIGINT,
        PRIMARY KEY (guild_id, role_id)
    )
""")


    # Dynamically add missing columns to channels table
    existing_cols = await bot.db.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'channels'")
    existing_cols = [col['column_name'] for col in existing_cols]

    if 'log_channel' not in existing_cols:
        await bot.db.execute("ALTER TABLE channels ADD COLUMN log_channel BIGINT DEFAULT NULL;")
        print("➕ Added 'log_channel' column to channels table.")

    if 'list_channel' not in existing_cols:
        await bot.db.execute("ALTER TABLE channels ADD COLUMN list_channel BIGINT DEFAULT NULL;")
        print("➕ Added 'list_channel' column to channels table.")

    # Dynamically create infractions table if missing
    table_check = await bot.db.fetch("SELECT to_regclass('public.infractions') AS exists")
    if not table_check[0]['exists']:
        await bot.db.execute("""
            CREATE TABLE infractions (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                mod_id BIGINT NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                timestamp BIGINT
            )
        """)
        print("✅ Created 'infractions' table dynamically.")

    print("✅ Database initialized!")

async def get_channel_id(bot, guild_id, channel_type):
    row = await bot.db.fetchrow(f"SELECT {channel_type} FROM channels WHERE guild_id = $1", guild_id)
    return row[channel_type] if row else None

async def set_channel_id(bot, guild_id, channel_type, channel_id):
    await bot.db.execute(f"""
        INSERT INTO channels (guild_id, {channel_type}) 
        VALUES ($1, $2)
        ON CONFLICT (guild_id) DO UPDATE 
        SET {channel_type} = EXCLUDED.{channel_type}
    """, guild_id, channel_id)

async def remove_channel_id(bot, guild_id, column_name):
    await bot.db.execute(f"UPDATE channels SET {column_name} = NULL WHERE guild_id = $1", guild_id)

async def ensure_guild_exists(bot, guild_id):
    await bot.db.execute("""
        INSERT INTO channels (guild_id)
        VALUES ($1)
        ON CONFLICT (guild_id) DO NOTHING
    """, guild_id)

async def heartbeat_task(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            heartbeat_channel_id = await get_channel_id(bot, guild.id, "heartbeat_channel")
            if heartbeat_channel_id:
                channel = bot.get_channel(heartbeat_channel_id)
                if channel:
                    await channel.send("💓 Heartbeat: Bot is still alive!")
        await asyncio.sleep(900)

async def log_infraction(bot, guild_id, user_id, mod_id, action, reason, timestamp):
    await bot.db.execute("""
        INSERT INTO infractions (guild_id, user_id, mod_id, action, reason, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, guild_id, user_id, mod_id, action, reason, timestamp)

async def get_infractions(bot, guild_id, user_id):
    rows = await bot.db.fetch("""
        SELECT id, guild_id, user_id, mod_id, action, reason, timestamp
        FROM infractions
        WHERE guild_id = $1 AND user_id = $2
        ORDER BY timestamp DESC
    """, guild_id, user_id)
    return [dict(r) for r in rows]

# ─── Autorole-related DB functions ─────────────────────────────────────────────

async def add_autorole(bot, guild_id: int, role_id: int):
    await bot.db.execute("""
        INSERT INTO autoroles (guild_id, role_id)
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING
    """, guild_id, role_id)

async def remove_autorole(bot, guild_id: int, role_id: int):
    await bot.db.execute("""
        DELETE FROM autoroles
        WHERE guild_id = $1 AND role_id = $2
    """, guild_id, role_id)

async def get_autoroles(bot, guild_id: int):
    rows = await bot.db.fetch("SELECT role_id FROM autoroles WHERE guild_id = $1", guild_id)
    return [r["role_id"] for r in rows]


