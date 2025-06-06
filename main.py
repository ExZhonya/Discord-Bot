# main.py
import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from db import database

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

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

@bot.event
async def on_ready():
    await database.initialize()
    print(f"Logged in as {bot.user}")


bot.run(TOKEN)
