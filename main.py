import discord, os, asyncio
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import View, Button

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
RULES_CHANNEL_ID = int(os.getenv('RULES_CHANNEL_ID', 0))
HEARTBEAT_CHANNEL_ID = int(os.getenv('HEARTBEAT_CHANNEL_ID', 0))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ---------------- Heartbeat Task ----------------

async def heartbeat_task():
    await bot.wait_until_ready()
    channel = bot.get_channel(HEARTBEAT_CHANNEL_ID)

    if not channel:
        print("Heartbeat channel not found. Check HEARTBEAT_CHANNEL_ID in .env.")
        return

    while not bot.is_closed():
        await channel.send("💓 Heartbeat: Bot is still alive!")
        await asyncio.sleep(900)

# ---------------- Events & Commands ----------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    bot.loop.create_task(heartbeat_task())

@bot.event
async def on_member_join(member):
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel:
        await welcome_channel.send(f"Welcome {member.mention} to the server! 🎉")

    rules_channel = bot.get_channel(RULES_CHANNEL_ID)
    if rules_channel:
        msg = await rules_channel.send(f"{member.mention}, please read the rules in this channel! 📜")
        await asyncio.sleep(10)
        await msg.delete()

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Bot Help Menu",
        description="Here are the available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(name=".help", value="Displays this help menu.", inline=False)
    embed.add_field(name=".ping", value="Checks the bot's latency.", inline=False)
    embed.add_field(name=".info", value="Provides server information.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def rules(ctx):
    if ctx.channel.id == RULES_CHANNEL_ID:
        embed = discord.Embed(
            title="Server Rules",
            color=discord.Color.blue()
        )
        embed.add_field(name="1. Respect everyone", value="Be respectful towards everyone.", inline=False)
        embed.add_field(name="2. No slurs", value="Do not use slurs or anything similar towards others.", inline=False)
        embed.add_field(name="3. Love the owner.", value="Because so.", inline=False)
        await ctx.send(embed=embed)
    else:
        msg = await ctx.send(f"Please use this command in <#{RULES_CHANNEL_ID}>!")
        await asyncio.sleep(5)
        await msg.delete()

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 Latency: {latency}ms")

@bot.command()
async def info(ctx):
    guild = ctx.guild
    num_roles = len(guild.roles)
    num_text_channels = len([channel for channel in guild.channels if isinstance(channel, discord.TextChannel)])
    num_voice_channels = len([channel for channel in guild.channels if isinstance(channel, discord.VoiceChannel)])
    created_at = guild.created_at.strftime("%B %d, %Y")

    embed = discord.Embed(
        title=f"Server Info - {guild.name}",
        color=discord.Color.green()
    )
    embed.add_field(name="Server Owner", value=guild.owner, inline=False)
    embed.add_field(name="Created On", value=created_at, inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    embed.add_field(name="Total Roles", value=num_roles, inline=False)
    embed.add_field(name="Text Channels", value=num_text_channels, inline=True)
    embed.add_field(name="Voice Channels", value=num_voice_channels, inline=True)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await ctx.send(embed=embed)

# ---------------- Game System ----------------

game_active = False
team = []
host = None
player_inventory = {}  # Stores player inventories

def team_members():
    return "\n".join(f"{idx + 1}. {name}" for idx, name in enumerate(team)) if team else "No members yet."

def generate_inventory(player_name):
    """Creates a default inventory for a new player."""
    player_inventory[player_name] = {
        "Weapon": None,
        "Armor": None,
        "Potion": None
    }

@bot.command()
async def startgame(ctx):
    global game_active, host
    if game_active:
        await ctx.send("A game is already active!")
        return
    
    team.clear()
    player_inventory.clear()
    game_active = True
    host = ctx.author.name  # Save the host's name
    
    embed = discord.Embed(
        title="Game Started!",
        description="A new game session has begun. Use `.join` to participate!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Current Team Members", value=team_members(), inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def join(ctx):
    global game_active
    if not game_active:
        await ctx.send("No active game! Use `.startgame` first.")
        return
    
    player_name = ctx.author.name  # Get the player's name
    if player_name in team:
        await ctx.send(f"{player_name}, you are already in the team!")
        return
    
    team.append(player_name)  # Add player to the team list
    generate_inventory(player_name)  # Create an inventory for the player

    embed = discord.Embed(
        title="New Player Joined!",
        description=f"{player_name} has joined the adventure! 🎉",
        color=discord.Color.green()
    )
    embed.add_field(name="Current Team Members", value=team_members(), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx, member: discord.Member = None):
    """Check a player's inventory."""
    player_name = member.name if member else ctx.author.name  # Get the target player's name
    
    if player_name not in player_inventory:
        await ctx.send(f"{player_name} has no inventory yet. Use `.join` first!")
        return
    
    inventory = player_inventory[player_name]
    inventory_text = "\n".join(f"{key}: {value if value else 'Empty'}" for key, value in inventory.items())

    embed = discord.Embed(
        title=f"{player_name}'s Inventory",
        description=inventory_text,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def endgame(ctx):
    global game_active, team, host, player_inventory
    if not game_active:
        await ctx.send("There is no active game to end.")
        return
    if ctx.author.name != host:
        await ctx.send("Only the host can end the game!")
        return
    
    game_active = False
    team.clear()
    player_inventory.clear()
    host = None
    embed = discord.Embed(
        title="Game Ended",
        description="The game session has been concluded.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)


bot.run(TOKEN)