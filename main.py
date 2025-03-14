import discord, os, asyncio
from dotenv import load_dotenv
from discord.ext import commands

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
async def start(ctx):
    if not game_active:
        await ctx.send("No active game! Use `.startgame` first.")
        return

    embed = discord.Embed(
        title="Game Menu",
        description="Choose an option:",
        color=discord.Color.blue()
    )
    embed.add_field(name="1️⃣ Start", value="Begin your adventure!", inline=False)
    embed.add_field(name="2️⃣ Shop", value="Buy equipment.", inline=False)
    embed.add_field(name="3️⃣ Inventory", value="Check your items.", inline=False)

    message = await ctx.send(embed=embed)

    reactions = ["1️⃣", "2️⃣", "3️⃣"]
    for reaction in reactions:
        await message.add_reaction(reaction)

    def check(reaction, user):
        return user == host and str(reaction.emoji) in reactions

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

        if str(reaction.emoji) == "2️⃣":
            await shop(ctx)
    except asyncio.TimeoutError:
        await ctx.send("Game menu timed out.")

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
    global host

    async def update_shop_menu(message, embed):
        await message.edit(embed=embed)
    
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

    def check(reaction, user):
        return user == host and str(reaction.emoji) in reactions

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

            if str(reaction.emoji) == "1️⃣":
                weapons_embed = discord.Embed(
                    title="Weapons Shop",
                    description="Available weapons:\n\n⚔️ Sword - 100g\n🏹 Bow - 150g\n🔨 Hammer - 200g\n\n🔙 Back",
                    color=discord.Color.dark_gold()
                )
                await update_shop_menu(message, weapons_embed)
            elif str(reaction.emoji) == "2️⃣":
                armors_embed = discord.Embed(
                    title="Armor Shop",
                    description="Available armor:\n\n🛡️ Chainmail - 200g\n🧥 Leather Armor - 150g\n👑 Helmet - 100g\n\n🔙 Back",
                    color=discord.Color.dark_gold()
                )
                await update_shop_menu(message, armors_embed)
            elif str(reaction.emoji) == "3️⃣":
                potions_embed = discord.Embed(
                    title="Potion Shop",
                    description="Available potions:\n\n❤️ Health Potion - 50g\n🌀 Mana Potion - 75g\n⚡ Stamina Potion - 60g\n\n🔙 Back",
                    color=discord.Color.dark_gold()
                )
                await update_shop_menu(message, potions_embed)
            elif str(reaction.emoji) == "4️⃣":
                await message.delete()
                await start(ctx)
                return
            
            # Add a back reaction when in submenus
            await message.clear_reactions()
            await message.add_reaction("🔙")

            def back_check(reaction, user):
                return user == host and str(reaction.emoji) == "🔙"

            await bot.wait_for("reaction_add", timeout=60.0, check=back_check)
            await update_shop_menu(message, embed)
            for reaction in reactions:
                await message.add_reaction(reaction)

        except asyncio.TimeoutError:
            await message.delete()
            return


bot.run(TOKEN)