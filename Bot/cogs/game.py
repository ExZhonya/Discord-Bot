# /cogs/game.py
import discord
from discord.ext import commands
from discord import app_commands
from utils.views import GameMenu

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    def get_game(self, guild_id):
        if guild_id not in self.games:
            self.games[guild_id] = {
                "active": False,
                "team": [],
                "host": None,
                "inventory": {},
                "gold": {},
                "has_started": False
            }
        return self.games[guild_id]

    # Slash Command: /game
    @app_commands.command(name="game", description="Start a new game session.")
    async def game_slash(self, interaction: discord.Interaction):
        await self.start_game(interaction.guild.id, interaction.user, interaction)

    @commands.command()
    async def game(self, ctx):
        await self.start_game(ctx.guild.id, ctx.author, ctx)

    async def start_game(self, guild_id, user, interaction_or_ctx):
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
            "has_started": False
        })

        embed = discord.Embed(
            title="Game Started! 🎮",
            description="A new game session has begun. Use `/join` or `.join` to participate!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Current Team Members", value="\n".join(game["team"]))
        await self._send(interaction_or_ctx, embed=embed)

    @app_commands.command(name="start", description="Start the game (host only)")
    async def start_slash(self, interaction: discord.Interaction):
        await self.open_menu(interaction.guild.id, interaction.user, interaction)

    @commands.command()
    async def start(self, ctx):
        await self.open_menu(ctx.guild.id, ctx.author, ctx)

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

    @app_commands.command(name="join", description="Join the game")
    async def join_slash(self, interaction: discord.Interaction):
        await self.join_game(interaction.guild.id, interaction.user, interaction)

    @commands.command()
    async def join(self, ctx):
        await self.join_game(ctx.guild.id, ctx.author, ctx)

    async def join_game(self, guild_id, user, interaction_or_ctx):
        game = self.get_game(guild_id)
        if not game["active"]:
            await self._send(interaction_or_ctx, "No active game! Use `/game` or `.game` first.")
            return
        if user.name in game["team"]:
            await self._send(interaction_or_ctx, f"{user.name}, you are already in the team!")
            return
        game["team"].append(user.name)
        game["inventory"][user.name] = {"Weapon": None, "Armor": None, "Potion": None}
        game["gold"][user.name] = 0
        embed = discord.Embed(
            title="New Player Joined! 🎉",
            description=f"{user.name} has joined the adventure!",
            color=discord.Color.green()
        )
        embed.add_field(name="Current Team Members", value="\n".join(game["team"]))
        await self._send(interaction_or_ctx, embed=embed)

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
        self.games.pop(guild_id)
        await self._send(interaction_or_ctx, embed=discord.Embed(title="Game Ended", description="The game session has been concluded.", color=discord.Color.red()))

    async def _send(self, ctx_or_interaction, content=None, embed=None, view=None):
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(content=content, embed=embed, view=view)
        else:
            await ctx_or_interaction.send(content=content, embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Game(bot))