import discord, os, asyncio, psycopg2
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import View, Button

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv("DATABASE_URL")  # Get PostgreSQL URL from Railway

# ---------------- PostgreSQL Database Setup ----------------
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        guild_id BIGINT PRIMARY KEY,
        welcome_channel BIGINT,
        rules_channel BIGINT,
        heartbeat_channel BIGINT
    )
""")
conn.commit()

# ---------------- Helper Functions ----------------
def set_channel(guild_id, key, channel_id):
    """Set a channel ID for a guild."""
    cursor.execute(f"""
        INSERT INTO channels (guild_id, {key}) 
        VALUES (%s, %s) 
        ON CONFLICT (guild_id) DO UPDATE SET {key} = EXCLUDED.{key}
    """, (guild_id, channel_id))
    conn.commit()

def get_channel(guild_id, key):
    """Get a channel ID for a guild."""
    cursor.execute(f"SELECT {key} FROM channels WHERE guild_id = %s", (guild_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# ---------------- Bot Setup ----------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ---------------- Heartbeat Task ----------------
async def heartbeat_task():
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        for guild in bot.guilds:
            channel_id = get_channel(guild.id, "heartbeat_channel")
            if channel_id:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send("💓 Heartbeat: Bot is still alive!")
        await asyncio.sleep(900)

# ---------------- Events & Commands ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    bot.loop.create_task(heartbeat_task())

@bot.event
async def on_member_join(member):
    """Welcome new members and send rules."""
    welcome_channel_id = get_channel(member.guild.id, "welcome_channel")
    rules_channel_id = get_channel(member.guild.id, "rules_channel")

    welcome_channel = bot.get_channel(welcome_channel_id) if welcome_channel_id else None
    rules_channel = bot.get_channel(rules_channel_id) if rules_channel_id else None

    if welcome_channel:
        await welcome_channel.send(f"Welcome {member.mention} to the server! 🎉")

    if rules_channel:
        msg = await rules_channel.send(f"{member.mention}, please read the rules in this channel! 📜")
        await asyncio.sleep(10)
        await msg.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx, channel_type: str, channel: discord.TextChannel):
    """Admin command to set a guild-specific channel type."""
    key = f"{channel_type.lower()}_channel"

    if key not in ["welcome_channel", "rules_channel", "heartbeat_channel"]:
        await ctx.send("Invalid channel type! Use: `WELCOME`, `RULES`, or `HEARTBEAT`.")
        return

    set_channel(ctx.guild.id, key, channel.id)
    await ctx.send(f"✅ {channel_type.capitalize()} channel set to {channel.mention}!")

@bot.command()
async def rules(ctx):
    """Show server rules."""
    rules_channel_id = get_channel(ctx.guild.id, "rules_channel")

    if ctx.channel.id == rules_channel_id:
        embed = discord.Embed(
            title="Server Rules",
            color=discord.Color.blue()
        )
        embed.add_field(name="1. Respect everyone", value="Be respectful towards everyone.", inline=False)
        embed.add_field(name="2. No slurs", value="Do not use slurs or anything similar towards others.", inline=False)
        embed.add_field(name="3. Love the owner.", value="Because so.", inline=False)
        await ctx.send(embed=embed)
    else:
        msg = await ctx.send(f"Please use this command in <#{rules_channel_id}>!")
        await asyncio.sleep(5)
        await msg.delete()

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 Latency: {latency}ms")

@bot.command()
async def info(ctx):
    guild = ctx.guild
    created_at = guild.created_at.strftime("%B %d, %Y")

    embed = discord.Embed(
        title=f"Server Info - {guild.name}",
        color=discord.Color.green()
    )
    embed.add_field(name="Server Owner", value=guild.owner, inline=False)
    embed.add_field(name="Created On", value=created_at, inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await ctx.send(embed=embed)

# ---------------- Game System ----------------
game_active = False
team = []
host = None

def team_members():
    return "\n".join(f"{i + 1}. {name}" for i, name in enumerate(team)) if team else "No members yet."

@bot.command()
async def game(ctx):
    global game_active, host
    if game_active:
        await ctx.send("A game is already active!")
        return

    team.clear()
    game_active = True
    host = ctx.author.name
    team.append(host)

    embed = discord.Embed(
        title="Game Started! 🎮",
        description="A new game session has begun. Use `.join` to participate!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Current Team Members", value=team_members(), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def join(ctx):
    if not game_active:
        await ctx.send("No active game! Use `.game` first.")
        return

    player_name = ctx.author.name
    if player_name in team:
        await ctx.send(f"{player_name}, you are already in the team!")
        return

    team.append(player_name)

    embed = discord.Embed(
        title="New Player Joined! 🎉",
        description=f"{player_name} has joined the adventure!",
        color=discord.Color.green()
    )
    embed.add_field(name="Current Team Members", value=team_members(), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def endgame(ctx):
    global game_active, team, host
    if not game_active:
        await ctx.send("There is no active game to end.")
        return
    if ctx.author.name != host:
        await ctx.send("Only the host can end the game!")
        return

    game_active = False
    team.clear()
    host = None
    embed = discord.Embed(
        title="Game Ended",
        description="The game session has been concluded.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

bot.run(TOKEN)
