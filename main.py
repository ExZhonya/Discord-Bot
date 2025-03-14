import discord, os, asyncio
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
RULES_CHANNEL_ID = int(os.getenv('RULES_CHANNEL_ID', 0))
HEARTBEAT_CHANNEL_ID = int(os.getenv('HEARTBEAT_CHANNEL_ID', 0))  # Add this to your .env file

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
        await asyncio.sleep(900)  # 900 seconds = 15 minutes OR change to 1500 for 25 minutes

# ---------------- Events & Commands ----------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    bot.loop.create_task(heartbeat_task())  # Start the heartbeat task

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

def team_members():
    return ", ".join(team) if team else "No members yet."

@bot.command()
async def startgame(ctx):
    global game_active, host
    team.clear()
    game_active = True
    host = ctx.author
    embed = discord.Embed(
        title="Game Started!",
        description="A new game session has begun. Use `.join` to participate!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Current Team Members", value=team_members(), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def join(ctx):
    if ctx.author.name not in team:
        team.append(ctx.author.name)
    embed = discord.Embed(
        title="Player Joined!",
        description=f"{ctx.author.mention} has joined the game!",
        color=discord.Color.green()
    )
    embed.add_field(name="Current Team Members", value=team_members(), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def shop(ctx):
    if not game_active:
        await ctx.send("No active game! Use `.startgame` first.")
        return
    if ctx.author != host:
        await ctx.send("Only the host can access the shop!")
        return
    
    embed = discord.Embed(
        title="Shop Menu",
        description="Choose a category:",
        color=discord.Color.purple()
    )
    embed.add_field(name="1️⃣ Weapons", value="Browse weapons.", inline=False)
    embed.add_field(name="2️⃣ Armors", value="Browse armors.", inline=False)
    embed.add_field(name="3️⃣ Potions", value="Browse potions.", inline=False)
    embed.add_field(name="4️⃣ Back/Exit", value="Return to the game menu.", inline=False)
    message = await ctx.send(embed=embed)
    
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    for reaction in reactions:
        await message.add_reaction(reaction)

@bot.command()
async def endgame(ctx):
    global game_active, team, host
    if not game_active:
        await ctx.send("There is no active game to end.")
        return
    if ctx.author != host:
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
