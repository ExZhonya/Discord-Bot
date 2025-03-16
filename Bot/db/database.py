import asyncpg
import asyncio

async def init_db(bot):
    from dotenv import load_dotenv
    import os
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')

    bot.db = await asyncpg.connect(DATABASE_URL)
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
