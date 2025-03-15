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
    
    class GameMenu(View):
        @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
        async def start_button(self, interaction: discord.Interaction, button: Button):
            await interaction.response.send_message("Adventure begins!")
        
        @discord.ui.button(label="Shop", style=discord.ButtonStyle.blurple)
        async def shop_button(self, interaction: discord.Interaction, button: Button):
            await shop(ctx)
        
        @discord.ui.button(label="Inventory", style=discord.ButtonStyle.gray)
        async def inventory_button(self, interaction: discord.Interaction, button: Button):
            await interaction.response.send_message("You checked your inventory!")
    
    await ctx.send(embed=embed, view=GameMenu())

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
    
    embed = discord.Embed(
        title="Shop Menu",
        description="Choose a category:",
        color=discord.Color.purple()
    )
    
    class ShopMenu(View):
        @discord.ui.button(label="Weapons", style=discord.ButtonStyle.primary)
        async def weapons_button(self, interaction: discord.Interaction, button: Button):
            weapons_embed = discord.Embed(
                title="Weapons Shop",
                description="⚔️ Sword - 100g\n🏹 Bow - 150g\n🔨 Hammer - 200g",
                color=discord.Color.dark_gold()
            )
            await interaction.response.edit_message(embed=weapons_embed, view=self)
        
        @discord.ui.button(label="Armors", style=discord.ButtonStyle.primary)
        async def armors_button(self, interaction: discord.Interaction, button: Button):
            armors_embed = discord.Embed(
                title="Armor Shop",
                description="🛡️ Chainmail - 200g\n🧥 Leather Armor - 150g\n👑 Helmet - 100g",
                color=discord.Color.dark_gold()
            )
            await interaction.response.edit_message(embed=armors_embed, view=self)
        
        @discord.ui.button(label="Potions", style=discord.ButtonStyle.primary)
        async def potions_button(self, interaction: discord.Interaction, button: Button):
            potions_embed = discord.Embed(
                title="Potion Shop",
                description="❤️ Health Potion - 50g\n🌀 Mana Potion - 75g\n⚡ Stamina Potion - 60g",
                color=discord.Color.dark_gold()
            )
            await interaction.response.edit_message(embed=potions_embed, view=self)
        
        @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
        async def back_button(self, interaction: discord.Interaction, button: Button):
            await interaction.response.edit_message(embed=embed, view=self)
    
    await ctx.send(embed=embed, view=ShopMenu())

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