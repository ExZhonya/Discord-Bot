# main.py
import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

keep_alive()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

@tasks.loop(minutes=1)
async def update_status():
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f".help"
    ))

@bot.event
async def setup_hook():
    for cog in [
        "cogs.general",
        "cogs.moderation",
        "cogs.events",
    ]:
        await bot.load_extension(cog)
    print("✅ All cogs loaded.")

bot.run(TOKEN)
