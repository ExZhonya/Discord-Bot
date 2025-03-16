import discord, os, asyncio
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import View, Button
import asyncpg

TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ---------------- Database Setup ----------------

async def init_db():
    bot.db = await asyncpg.connect(DATABASE_URL)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            guild_id BIGINT PRIMARY KEY,
            welcome_channel BIGINT DEFAULT NULL,
            rules_channel BIGINT DEFAULT NULL,
            heartbeat_channel BIGINT DEFAULT NULL
        )
    """)

async def get_channel_id(guild_id, channel_type):
    row = await bot.db.fetchrow(f"SELECT {channel_type} FROM channels WHERE guild_id = $1", guild_id)
    return row[channel_type] if row else None

async def set_channel_id(guild_id, channel_type, channel_id):
    await bot.db.execute(f"""
        INSERT INTO channels (guild_id, {channel_type}) 
        VALUES ($1, $2)
        ON CONFLICT (guild_id) DO UPDATE 
        SET {channel_type} = EXCLUDED.{channel_type}
    """, guild_id, channel_id)

# ---------------- Heartbeat System ----------------

async def heartbeat_task():
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        for guild in bot.guilds:
            heartbeat_channel_id = await get_channel_id(guild.id, "heartbeat_channel")
            if heartbeat_channel_id:
                channel = bot.get_channel(heartbeat_channel_id)
                if channel:
                    await channel.send("💓 Heartbeat: Bot is still alive!")
        await asyncio.sleep(900)

# ---------------- Status ----------------

@bot.event
async def on_ready():
    await init_db()
    print(f"✅ Logged in as {bot.user}!")
    bot.loop.create_task(heartbeat_task())

# ---------------- Help Commands ----------------
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
    embed.add_field(name=".gamehelp", value="List of Game's commands.", inline=False)
    embed.add_field(name=".channelhelp", value="(Admin) Set welcome, rules, or heartbeat channels.", inline=False)
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
async def channelhelp(ctx):
    embed = discord.Embed(
        title="Set Channel Help",
        color=discord.Color.blue()
    )

    embed.add_field(name=".setchannel welcome", value="Set your welcome channel.")
    embed.add_field(name=".setchannel rules", value="Set your rules channel. use `.rules` to make a fix preset of rules.(TBC Soon)")
    embed.add_field(name=".setchannel heartbeat", value="Set a heartbeat message of the bot's Online.")
    await ctx.send(embed=embed)

# ---------------- Events & Commands ----------------

@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    welcome_channel_id = await get_channel_id(guild_id, "welcome_channel")
    rules_channel_id = await get_channel_id(guild_id, "rules_channel")

    if welcome_channel_id:
        welcome_channel = bot.get_channel(welcome_channel_id)
        if welcome_channel:
            await welcome_channel.send(f"🎉 Welcome {member.mention} to the server!")

    if rules_channel_id:
        rules_channel = bot.get_channel(rules_channel_id)
        if rules_channel:
            msg = await rules_channel.send(f"📜 {member.mention}, please read the rules!")
            await asyncio.sleep(10)
            await msg.delete()

@bot.command()
async def setchannel(ctx, channel_type: str, channel: discord.TextChannel):
    if ctx.author.guild_permissions.administrator:
        if channel_type.lower() not in ["welcome", "rules", "heartbeat"]:
            await ctx.send("❌ Invalid type! Use `welcome`, `rules`, or `heartbeat`.")
            return
        
        column_name = f"{channel_type.lower()}_channel"
        await set_channel_id(ctx.guild.id, column_name, channel.id)
        await ctx.send(f"✅ {channel_type.capitalize()} channel set to {channel.mention}!")
    else:
        await ctx.send("❌ You need admin permissions!")

@bot.command()
async def rules(ctx):
    rules_channel_id = await get_channel_id(ctx.guild.id, "rules_channel")
    if ctx.channel.id == rules_channel_id:
        embed = discord.Embed(
            title="Server Rules",
            color=discord.Color.blue()
        )
        embed.add_field(name="1. Respect everyone", value="Be respectful towards everyone.", inline=False)
        embed.add_field(name="2. No slurs", value="Do not use slurs or anything similar towards others.", inline=False)
        embed.add_field(name="3. Love the owner.", value="Because i say so.", inline=False)
        await ctx.send(embed=embed)
    else:
        msg = await ctx.send(f"⚠️ Use this command in <#{rules_channel_id}>!")
        await asyncio.sleep(5)
        await msg.delete()

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.command()
async def info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📌 Server Info - {guild.name}", color=discord.Color.green())
    embed.add_field(name="Owner", value=guild.owner, inline=False)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%B %d, %Y"), inline=False)
    embed.add_field(name="Members", value=guild.member_count, inline=False)
    embed.add_field(name="Roles", value=len(guild.roles), inline=False)
    embed.add_field(name="Text Channels", value=len([ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]), inline=True)
    embed.add_field(name="Voice Channels", value=len([ch for ch in guild.channels if isinstance(ch, discord.VoiceChannel)]), inline=True)
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await ctx.send(embed=embed)

# ---------------- Game System ----------------

games = {}  # Dictionary to store game data per server

def get_game(guild_id):
    """Retrieve or initialize a game session for the guild."""
    if guild_id not in games:
        games[guild_id] = {
            "active": False,
            "team": [],
            "host": None,
            "inventory": {},  # Stores items per player
            "gold": {}  # Gold balance per player
        }
    return games[guild_id]

@bot.command()
async def game(ctx):
    guild_id = ctx.guild.id
    game = get_game(guild_id)

    if game["active"]:
        await ctx.send("A game is already active in this server!")
        return

    game["team"].clear()
    game["active"] = True
    game["host"] = ctx.author.name
    game["team"].append(game["host"])
    game["inventory"] = {}  # Reset inventory for a new game
    game["gold"] = {}  # Reset gold balance for a new game

    # Initialize gold & inventory for the host
    game["inventory"][ctx.author.name] = {"Weapon": None, "Armor": None, "Potion": None}
    game["gold"][ctx.author.name] = 0

    embed = discord.Embed(
        title="Game Started! 🎮",
        description="A new game session has begun. Use `.join` to participate!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Current Team Members", value="\n".join(game["team"]), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def start(ctx):
    """Opens the Game Menu if a game is active."""
    guild_id = ctx.guild.id
    game = get_game(guild_id)
    
    if not game["active"]:
        await ctx.send("No active game! Use `.game` first.", delete_after=3)
        return
    
    if ctx.author.name != game["host"]:
        await ctx.send("Only the host can start the game!", delete_after=3)
        return

    await show_game_menu(ctx)

async def show_game_menu(ctx):
    """Displays the main game menu with options."""
    embed = discord.Embed(
        title="Game Menu",
        description="Choose an option:",
        color=discord.Color.blue()
    )

    class GameMenu(View):
        @discord.ui.button(label="Start Adventure", style=discord.ButtonStyle.green)
        async def start_button(self, interaction: discord.Interaction, button: Button):
            guild_id = interaction.guild.id
            game = get_game(guild_id)
            if interaction.user.name != game["host"]:
                await interaction.response.send_message("Only the host can start!", ephemeral=True)
                return
            await interaction.message.delete()
            await interaction.channel.send("🌍 The adventure begins!")

        @discord.ui.button(label="Shop", style=discord.ButtonStyle.blurple)
        async def shop_button(self, interaction: discord.Interaction, button: Button):
            guild_id = interaction.guild.id
            game = get_game(guild_id)
            if interaction.user.name != game["host"]:
                await interaction.response.send_message("Only the host can access the shop!", ephemeral=True)
                return
            await interaction.message.delete()
            await show_shop(interaction.channel)

        @discord.ui.button(label="Inventory", style=discord.ButtonStyle.gray)
        async def inventory_button(self, interaction: discord.Interaction, button: Button):
            guild_id = interaction.guild.id
            game = get_game(guild_id)
            if interaction.user.name != game["host"]:
                await interaction.response.send_message("Only the host can check the inventory!", ephemeral=True)
                return
            await interaction.message.delete()
            await show_inventory(interaction.channel)

    await ctx.send(embed=embed, view=GameMenu())

@bot.command()
async def join(ctx):
    guild_id = ctx.guild.id
    game = get_game(guild_id)

    if not game["active"]:
        await ctx.send("No active game! Use `.game` first.")
        return

    player_name = ctx.author.name
    if player_name in game["team"]:
        await ctx.send(f"{player_name}, you are already in the team!")
        return

    game["team"].append(player_name)
    game["inventory"][player_name] = {"Weapon": None, "Armor": None, "Potion": None}
    game["gold"][player_name] = 0  # New player starts with 0 gold

    embed = discord.Embed(
        title="New Player Joined! 🎉",
        description=f"{player_name} has joined the adventure!",
        color=discord.Color.green()
    )
    embed.add_field(name="Current Team Members", value="\n".join(game["team"]), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def gold(ctx):
    """Shows the player's current gold balance."""
    guild_id = ctx.guild.id
    game = get_game(guild_id)
    player_name = ctx.author.name

    gold = game["gold"].get(player_name, 0)
    await ctx.send(f"💰 {player_name}, you have **{gold} gold**.")

async def show_inventory(channel):
    guild_id = channel.guild.id
    game = get_game(guild_id)
    inventory = game["inventory"]
    gold = game["gold"]

    embed = discord.Embed(title="Inventory List", color=discord.Color.blue())

    for player, items in inventory.items():
        embed.add_field(
            name=f"{player} (💰 {gold.get(player, 0)} gold)",
            value=f"**Weapon:** {items['Weapon'] or 'None'}\n"
                  f"**Armor:** {items['Armor'] or 'None'}\n"
                  f"**Potion:** {items['Potion'] or 'None'}",
            inline=False
        )

    class InventoryMenu(View):
        @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
        async def back_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await show_game_menu(interaction.channel)

    await channel.send(embed=embed, view=InventoryMenu())

async def show_shop(channel):
    guild_id = channel.guild.id
    game = get_game(guild_id)

    embed = discord.Embed(
        title="Shop Menu",
        description="Choose a category:",
        color=discord.Color.purple()
    )

    class ShopMenu(View):
        @discord.ui.button(label="Weapons", style=discord.ButtonStyle.primary)
        async def weapons_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await show_weapon_shop(interaction.channel, interaction.user.name, guild_id)

        @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
        async def back_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await show_game_menu(interaction.channel)

    await channel.send(embed=embed, view=ShopMenu())

async def show_weapon_shop(channel, player_name, guild_id):
    """Displays the weapon shop and allows players to buy weapons."""
    game = get_game(guild_id)

    weapons = {
        "Sword": 100,
        "Bow": 150,
        "Hammer": 200
    }

    embed = discord.Embed(title="Weapons Shop ⚔️", description="Choose an item to buy:", color=discord.Color.dark_gold())
    for weapon, price in weapons.items():
        embed.add_field(name=weapon, value=f"💰 {price} gold", inline=False)

    class WeaponShop(View):
        @discord.ui.button(label="Buy Sword (100g)", style=discord.ButtonStyle.green)
        async def buy_sword(self, interaction: discord.Interaction, button: Button):
            await buy_item(interaction, player_name, guild_id, "Sword", 100)

        @discord.ui.button(label="Buy Bow (150g)", style=discord.ButtonStyle.green)
        async def buy_bow(self, interaction: discord.Interaction, button: Button):
            await buy_item(interaction, player_name, guild_id, "Bow", 150)

        @discord.ui.button(label="Buy Hammer (200g)", style=discord.ButtonStyle.green)
        async def buy_hammer(self, interaction: discord.Interaction, button: Button):
            await buy_item(interaction, player_name, guild_id, "Hammer", 200)

        @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
        async def back_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            await show_shop(interaction.channel)

    await channel.send(embed=embed, view=WeaponShop())

async def buy_item(interaction, player_name, guild_id, item_name, price):
    """Handles buying an item from the shop."""
    game = get_game(guild_id)
    player_gold = game["gold"].get(player_name, 0)

    if player_gold < price:
        await interaction.response.send_message(f"❌ You don't have enough gold! ({player_gold}g)", ephemeral=True)
        return

    game["gold"][player_name] -= price
    game["inventory"][player_name]["Weapon"] = item_name

    await interaction.response.send_message(f"✅ {player_name} bought a **{item_name}** for {price} gold!", ephemeral=False)

@bot.command()
async def addgold(ctx, amount: int):
    """Adds gold to a player's balance (Admin only)."""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need admin permissions to use this command.")
        return

    guild_id = ctx.guild.id
    player_name = ctx.author.name
    game = get_game(guild_id)

    game["gold"][player_name] = game["gold"].get(player_name, 0) + amount
    await ctx.send(f"💰 {player_name} now has {game['gold'][player_name]} gold!")

@bot.command()
async def endgame(ctx):
    guild_id = ctx.guild.id
    game = get_game(guild_id)

    if not game["active"]:
        await ctx.send("There is no active game to end.")
        return
    if ctx.author.name != game["host"]:
        await ctx.send("Only the host can end the game!")
        return

    games.pop(guild_id, None)  # Completely remove game data for this server

    embed = discord.Embed(
        title="Game Ended",
        description="The game session has been concluded.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)


bot.run(TOKEN)
