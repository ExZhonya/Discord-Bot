# main.py
import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from db.database import init_db, heartbeat_task

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

@bot.event
async def on_ready():
    await init_db(bot)
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}!")
    bot.loop.create_task(heartbeat_task(bot))
    update_status.start()

@tasks.loop(minutes=1)
async def update_status():
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"𝗪𝗮𝘁𝗰𝗵𝗶𝗻𝗴 𝘁𝗵𝗲 𝘀𝗲𝗿𝘃𝗲𝗿𝘀."
    ))

@bot.event
async def setup_hook():
    for cog in [
        "cogs.general",
        "cogs.moderation",
        "cogs.events",
        "cogs.game"
    ]:
        await bot.load_extension(cog)
    print("✅ All cogs loaded.")

bot.run(TOKEN)
