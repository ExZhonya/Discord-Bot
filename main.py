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
    embed.add_field(name=".gamehelp", value="List of Game's commands", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def gamehelp(ctx):
    embed = discord.Embed(
        title="Game Help",
        color=discord.Color.blue()
    )
    
    embed.add_field(name=".game", value="Use this to start a game.", inline=False)
    embed.add_field(name=".start", value="Use this to open the Game Menu.", inline=False)
    embed.add_field(name=".endgame", value="Use this to end an existing game.", inline=False)
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
async def start(ctx):
    if not game_active:
        await ctx.send("No active game! Use `.game` first.")
        return

    await show_game_menu(ctx)

async def show_game_menu(ctx):
    embed = discord.Embed(
        title="Game Menu",
        description="Choose an option:",
        color=discord.Color.blue()
    )

    class GameMenu(View):
        @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
        async def start_button(self, interaction: discord.Interaction, button: Button):
            if interaction.user.name != host:
                await interaction.response.send_message("Only the host can start!", ephemeral=True)
                return
            await interaction.message.delete()
            await interaction.channel.send("Adventure begins!")

        @discord.ui.button(label="Shop", style=discord.ButtonStyle.blurple)
        async def shop_button(self, interaction: discord.Interaction, button: Button):
            if interaction.user.name != host:
                await interaction.response.send_message("Only the host can access the shop!", ephemeral=True)
                return
            await interaction.message.delete()
            await show_shop(interaction.channel)

        @discord.ui.button(label="Inventory", style=discord.ButtonStyle.gray)
        async def inventory_button(self, interaction: discord.Interaction, button: Button):
            if interaction.user.name != host:
                await interaction.response.send_message("Only the host can check the inventory!", ephemeral=True)
                return
            await interaction.message.delete()
            await show_inventory(interaction.channel)

    msg = await ctx.send(embed=embed, view=GameMenu())
    await delete_previous(ctx, msg)

async def show_inventory(channel):
    embed = discord.Embed(title="Inventory List", color=discord.Color.blue())

    for i, player in enumerate(team, start=1):
        embed.add_field(
            name=f"{i}. {player}",
            value="**Weapon:** None\n**Armor:** None\n**Potion:** None",
            inline=False
        )

    class InventoryMenu(View):
        @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
        async def back_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await show_game_menu(interaction.channel)

    msg = await channel.send(embed=embed, view=InventoryMenu())
    await delete_previous(channel, msg)

async def show_shop(channel):
    embed = discord.Embed(
        title="Shop Menu",
        description="Choose a category:",
        color=discord.Color.purple()
    )

    class ShopMenu(View):
        @discord.ui.button(label="Weapons", style=discord.ButtonStyle.primary)
        async def weapons_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await channel.send(embed=discord.Embed(
                title="Weapons Shop",
                description="⚔️ Sword - 100g\n🏹 Bow - 150g\n🔨 Hammer - 200g",
                color=discord.Color.dark_gold()
            ), view=self)

        @discord.ui.button(label="Armors", style=discord.ButtonStyle.primary)
        async def armors_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await channel.send(embed=discord.Embed(
                title="Armor Shop",
                description="🛡️ Chainmail - 200g\n🧥 Leather Armor - 150g\n👑 Helmet - 100g",
                color=discord.Color.dark_gold()
            ), view=self)

        @discord.ui.button(label="Potions", style=discord.ButtonStyle.primary)
        async def potions_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await channel.send(embed=discord.Embed(
                title="Potion Shop",
                description="❤️ Health Potion - 50g\n🌀 Mana Potion - 75g\n⚡ Stamina Potion - 60g",
                color=discord.Color.dark_gold()
            ), view=self)

        @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
        async def back_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await show_game_menu(interaction.channel)

    msg = await channel.send(embed=embed, view=ShopMenu())
    await delete_previous(channel, msg)

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

async def delete_previous(ctx, msg):
    async for message in ctx.channel.history(limit=5):
        if message.author == bot.user and message.id != msg.id:
            await message.delete()


bot.run(TOKEN)