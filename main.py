import discord, os, asyncio
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
RULES_CHANNEL_ID = int(os.getenv('RULES_CHANNEL_ID', 0))
HEARTBEAT_CHANNEL_ID = int(os.getenv('HEARTBEAT_CHANNEL_ID', 0))

game_sessions = {}

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
    embed = discord.Embed(
        title=f"Server Info - {guild.name}",
        color=discord.Color.green()
    )
    embed.add_field(name="Server Owner", value=guild.owner, inline=False)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%B %d, %Y"), inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    embed.add_field(name="Total Roles", value=len(guild.roles), inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

# ---------------- Game System ----------------

@bot.command()
async def startgame(ctx):
    if ctx.channel.id in game_sessions:
        await ctx.send("A game is already in progress in this channel!")
        return
    game_sessions[ctx.channel.id] = {}
    await ctx.send("Game session started! Players, use `.join` to participate.")

@bot.command()
async def join(ctx):
    if ctx.channel.id not in game_sessions:
        await ctx.send("No active game session! Use `.startgame` first.")
        return
    game_sessions[ctx.channel.id][ctx.author.id] = {'hp': 100}
    await ctx.send(f"{ctx.author.mention} has joined the game!")

@bot.command()
async def attack(ctx, target: discord.Member):
    if ctx.channel.id not in game_sessions or ctx.author.id not in game_sessions[ctx.channel.id]:
        await ctx.send("You are not in a game! Use `.join` to participate.")
        return
    if target.id not in game_sessions[ctx.channel.id]:
        await ctx.send("Target is not in the game!")
        return
    damage = 20  # Fixed damage for now
    game_sessions[ctx.channel.id][target.id]['hp'] -= damage
    await ctx.send(f"{ctx.author.mention} attacked {target.mention} for {damage} damage!")
    if game_sessions[ctx.channel.id][target.id]['hp'] <= 0:
        await ctx.send(f"{target.mention} has been defeated!")
        del game_sessions[ctx.channel.id][target.id]

@bot.command()
async def forfeit(ctx):
    if ctx.channel.id in game_sessions:
        del game_sessions[ctx.channel.id]
        await ctx.send("Game session has been reset. You can start a new game using `.startgame`.")
    else:
        await ctx.send("No active game session to forfeit.")

bot.run(TOKEN)
