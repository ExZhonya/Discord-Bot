# /cogs/game.py
import discord, os, json
from discord.ext import commands
from discord import app_commands
from utils.views import GameMenu

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    def get_game(self, guild_id):
        """Loads the game data from a file to ensure persistence."""
        file_path = "data/game_data.json"

        # Ensure "data/" directory exists
        if not os.path.exists("data"):
            os.makedirs("data")

        # Load existing game data or create a new file
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                try:
                    self.games = json.load(f)
                except json.JSONDecodeError:
                    self.games = {}  # Reset if file is corrupted
        else:
            self.games = {}
            with open(file_path, "w") as f:
                json.dump({}, f)  # Create an empty game_data.json

        # Ensure guild_id has a game state
        if guild_id not in self.games:
            print(f"⚠️ get_game() is creating a new game state for {guild_id}!")  
            self.games[guild_id] = {
                "active": False,
                "team": [],
                "host": None,
                "inventory": {},
                "gold": {},
                "team_data": {},
                "has_started": False,
                "visibility": None  
            }

        return self.games[guild_id]
    
    def default_player_data(self):
        return {
            "class": None,
            "stats": {
                "HP": 100,
                "MP": 50,
                "Str": 1,
                "Int": 1,
                "Def": 1,
                "Dex": 1,
                "StatPoints": 1,
                "EXP": 0
            }
        }

    @app_commands.command(name="game", description="Start a new game session.")
    @app_commands.choices(visibility=[
        app_commands.Choice(name="Public (Admin-only commands)", value="public"),
        app_commands.Choice(name="Private (Host-only commands)", value="private")
    ])
    async def game_slash(self, interaction: discord.Interaction, visibility: app_commands.Choice[str]):
        await self.start_game(interaction.guild.id, interaction.user, interaction, visibility.value)

    @commands.command()
    async def game(self, ctx, visibility: str = None):
        if not visibility or visibility.lower() not in ["public", "private"]:
            await ctx.send("⚠️ Please specify visibility: `public` or `private`. Example: `.game public`")
            return
        await self.start_game(ctx.guild.id, ctx.author, ctx, visibility.lower())


    async def start_game(self, guild_id, user, interaction_or_ctx, visibility):
        game = self.get_game(guild_id)
        if game["active"]:
            await self._send(interaction_or_ctx, "A game is already active in this server!")
            return

        game.update({
            "active": True,
            "team": [user.name],
            "host": user.name,
            "inventory": {user.name: {"Weapon": None, "Armor": None, "Potion": None}},
            "gold": {user.name: 0},
            "team_data": {user.name: self.default_player_data()},
            "has_started": False,
            "visibility": visibility
        })

        embed = discord.Embed(
            title="Game Started! 🎮",
            description=f"A new **{visibility.capitalize()}** game session has begun. Use `/join` or `.join` to participate!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Current Team Members", value="\n".join(game["team"]))
        await self._send(interaction_or_ctx, embed=embed)

    @app_commands.command(name="start", description="Start the game (host only)")
    async def start_slash(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        user = interaction.user
        game = self.get_game(guild_id)

        if not game["active"]:
            await self._send(interaction, "No active game! Use `/game` or `.game` first.")
            return
        if user.name != game["host"]:
            await self._send(interaction, "Only the host can start the game!")
            return
        if game["has_started"]:
            await self._send(interaction, "The game has already started!")
            return
        game["has_started"] = True

        await self.open_menu(guild_id, user, interaction)


    @commands.command()
    async def start(self, ctx):
        guild_id = ctx.guild.id
        user = ctx.author
        game = self.get_game(guild_id)

        if not game["active"]:
            await self._send(ctx, "No active game! Use `/game` or `.game` first.")
            return
        if user.name != game["host"]:
            await self._send(ctx, "Only the host can start the game!")
            return
        if game["has_started"]:
            await self._send(ctx, "The game has already started!")
            return
        game["has_started"] = True

        await self.open_menu(guild_id, user, ctx)


    @app_commands.command(name="menu", description="Open the game menu (host only)")
    async def menu_slash(self, interaction: discord.Interaction):
        await self.open_menu(interaction.guild.id, interaction.user, interaction)

    @commands.command()
    async def menu(self, ctx):
        await self.open_menu(ctx.guild.id, ctx.author, ctx)

    async def open_menu(self, guild_id, user, interaction_or_ctx):
        game = self.get_game(guild_id)
        if not game["active"]:
            await self._send(interaction_or_ctx, "No active game! Use `/game` or `.game` first.")
            return
        if user.name != game["host"]:
            await self._send(interaction_or_ctx, "Only the host can open the menu!")
            return
        await self._send(interaction_or_ctx, embed=discord.Embed(title="Game Menu", description="Choose an option:", color=discord.Color.blue()), view=GameMenu(interaction_or_ctx, game))

# ---------------- Join Commands ----------------

    @app_commands.command(name="join", description="Join the game")
    async def join_slash(self, interaction: discord.Interaction):
        await self.join_game(interaction.guild.id, interaction.user, interaction)

    def save_game(self):
        """Saves the current game state to a file."""
        file_path = "data/game_data.json"

        # Ensure "data/" directory exists
        if not os.path.exists("data"):
            os.makedirs("data")

        with open(file_path, "w") as f:
            json.dump(self.games, f, indent=4)

    @commands.command(name="join")  
    async def join(self, ctx):  # ✅ Proper `.join` command
        await self.join_game(ctx.guild.id, ctx.author, ctx)  # ✅ Calls `join_game()` with the correct arguments

    
    async def join_game(self, guild_id, user, interaction_or_ctx):
        game = self.get_game(guild_id)

        if not game["active"]:
            await self._send(interaction_or_ctx, "No active game! Use `/game` or `.game` first.")
            return
        if game["has_started"]:
            await self._send(interaction_or_ctx, "A game is already active in this server!")
            return
        if user.name in game["team"]:
            await self._send(interaction_or_ctx, f"{user.name}, you are already in the team!")
            return

        game["team"].append(user.name)
        game["inventory"][user.name] = {"Weapon": None, "Armor": None, "Potion": None}
        game["gold"][user.name] = 0
        game["team_data"][user.name] = self.default_player_data()

        self.save_game()  # Save after updating

        embed = discord.Embed(
            title="New Player Joined! 🎉",
            description=f"{user.name} has joined the adventure!",
            color=discord.Color.green()
        )
        embed.add_field(name="Current Team Members", value="\n".join(game["team"]))
        await self._send(interaction_or_ctx, embed=embed)

# ---------------- Gold Commands ----------------

    @app_commands.command(name="addgold", description="Give gold to a player (requires @user and amount)")
    @app_commands.describe(user="Mention a player", amount="Amount of gold (required)")
    async def addgold_slash(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await self.add_gold(interaction.guild.id, interaction.user, interaction, user, amount)

    @commands.command()
    async def addgold(self, ctx, member: discord.Member = None, amount: int = None):
        if not member or amount is None:
            await ctx.send("⚠️ Usage: `.addgold @user <amount>`")
            return
        await self.add_gold(ctx.guild.id, ctx.author, ctx, member, amount)

    async def add_gold(self, guild_id, caller, interaction_or_ctx, target_user, amount):
        game = self.get_game(guild_id)

        if not game["active"]:
            await self._send(interaction_or_ctx, "No active game session.")
            return

        if game["visibility"] == "public":
            if not caller.guild_permissions.administrator:
                await self._send(interaction_or_ctx, "❌ Only an admin can add gold in a public game.")
                return
        elif game["visibility"] == "private":
            if caller.name != game["host"]:
                await self._send(interaction_or_ctx, "❌ Only the host can add gold in a private game.")
                return

        if target_user.name not in game["gold"]:
            game["gold"][target_user.name] = 0
        game["gold"][target_user.name] += amount

        embed = discord.Embed(
            title="💰 Gold Added",
            description=f"{caller.name} gave **{amount} gold** to {target_user.name}.",
            color=discord.Color.green()
        )
        embed.add_field(name="New Balance", value=f"{target_user.name} now has **{game['gold'][target_user.name]} gold**.", inline=False)

        await self._send(interaction_or_ctx, embed=embed)

    async def _send(self, ctx_or_interaction, content=None, embed=None, view=None):
        guild_id = ctx_or_interaction.guild.id if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.guild.id
        if guild_id in self.last_message:
            try:
                await self.last_message[guild_id].delete()
            except:
                pass

        if isinstance(ctx_or_interaction, discord.Interaction):
            msg = await ctx_or_interaction.channel.send(content=content, embed=embed, view=view)
        else:
            msg = await ctx_or_interaction.send(content=content, embed=embed, view=view)

        self.last_message[guild_id] = msg

    @app_commands.command(name="gold", description="Check your current gold")
    async def gold_slash(self, interaction: discord.Interaction):
        await self.check_gold(interaction.guild.id, interaction.user, interaction)

    @commands.command()
    async def gold(self, ctx):
        await self.check_gold(ctx.guild.id, ctx.author, ctx)

    async def check_gold(self, guild_id, user, interaction_or_ctx):
        game = self.get_game(guild_id)
        gold = game["gold"].get(user.name, 0)
        await self._send(interaction_or_ctx, f"💰 {user.name}, you have **{gold} gold**.")

# ---------------- End Commands ----------------

    @app_commands.command(name="endgame", description="End the game (host only)")
    async def endgame_slash(self, interaction: discord.Interaction):
        await self.end_game(interaction.guild.id, interaction.user, interaction)

    @commands.command()
    async def endgame(self, ctx):
        await self.end_game(ctx.guild.id, ctx.author, ctx)

    async def end_game(self, guild_id, user, interaction_or_ctx):
        game = self.get_game(guild_id)

        if not game["active"]:
            await self._send(interaction_or_ctx, "There is no active game to end.")
            return
        if user.name != game["host"]:
            await self._send(interaction_or_ctx, "Only the host can end the game!")
            return

        # Remove game data from memory
        if guild_id in self.games:
            self.games.pop(guild_id)

        # Delete saved game data file (optional: reset instead of delete)
        file_path = "data/game_data.json"
        if os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump({}, f, indent=4)  # Resets the file with an empty dictionary

        self.games = {}

        await self._send(interaction_or_ctx, embed=discord.Embed(
            title="Game Ended",
            description="The game session has been concluded.",
            color=discord.Color.red()
        ))

    async def _send(self, ctx_or_interaction, content=None, embed=None, view=None):
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(content=content, embed=embed, view=view)
        else:
            await ctx_or_interaction.send(content=content, embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Game(bot))