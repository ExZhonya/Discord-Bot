# /cogs/game.py
import discord
from discord.ext import commands
from utils.views import GameMenu, ShopMenu, InventoryMenu, WeaponShop

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # Dictionary to store game data per guild

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

    @commands.command()
    async def game(self, ctx):
        guild_id = ctx.guild.id
        game = self.get_game(guild_id)

        if game["active"]:
            await ctx.send("A game is already active in this server!")
            return

        game.update({
            "active": True,
            "team": [ctx.author.name],
            "host": ctx.author.name,
            "inventory": {ctx.author.name: {"Weapon": None, "Armor": None, "Potion": None}},
            "gold": {ctx.author.name: 0},
            "has_started": False
        })

        embed = discord.Embed(
            title="Game Started! 🎮",
            description="A new game session has begun. Use `.join` to participate!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Current Team Members", value="\n".join(game["team"]))
        await ctx.send(embed=embed)

    @commands.command()
    async def start(self, ctx):
        game = self.get_game(ctx.guild.id)
        if not game["active"]:
            await ctx.send("No active game! Use `.game` first.")
            return
        if ctx.author.name != game["host"]:
            await ctx.send("Only the host can start the game!")
            return
        if game["has_started"]:
            await ctx.send("This session has already been started. Use `.menu` instead.")
            return
        game["has_started"] = True
        await ctx.send(embed=discord.Embed(title="Game Menu", description="Choose an option:", color=discord.Color.blue()), view=GameMenu(ctx, self))

    @commands.command()
    async def menu(self, ctx):
        game = self.get_game(ctx.guild.id)
        if not game["active"]:
            await ctx.send("No active game! Use `.game` first.")
            return
        if ctx.author.name != game["host"]:
            await ctx.send("Only the host can open the menu!")
            return
        await ctx.send(embed=discord.Embed(title="Game Menu", description="Choose an option:", color=discord.Color.blue()), view=GameMenu(ctx, self))

    @commands.command()
    async def join(self, ctx):
        game = self.get_game(ctx.guild.id)
        player_name = ctx.author.name

        if not game["active"]:
            await ctx.send("No active game! Use `.game` first.")
            return
        if player_name in game["team"]:
            await ctx.send(f"{player_name}, you are already in the team!")
            return

        game["team"].append(player_name)
        game["inventory"][player_name] = {"Weapon": None, "Armor": None, "Potion": None}
        game["gold"][player_name] = 0

        embed = discord.Embed(
            title="New Player Joined! 🎉",
            description=f"{player_name} has joined the adventure!",
            color=discord.Color.green()
        )
        embed.add_field(name="Current Team Members", value="\n".join(game["team"]))
        await ctx.send(embed=embed)

    @commands.command()
    async def gold(self, ctx):
        game = self.get_game(ctx.guild.id)
        player_name = ctx.author.name
        gold = game["gold"].get(player_name, 0)
        await ctx.send(f"💰 {player_name}, you have **{gold} gold**.")

    @commands.command()
    async def addgold(self, ctx, amount: int):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You need admin permissions to use this command.")
            return
        game = self.get_game(ctx.guild.id)
        player_name = ctx.author.name
        game["gold"][player_name] = game["gold"].get(player_name, 0) + amount
        await ctx.send(f"💰 {player_name} now has {game['gold'][player_name]} gold!")

    @commands.command()
    async def endgame(self, ctx):
        guild_id = ctx.guild.id
        game = self.get_game(guild_id)
        if not game["active"]:
            await ctx.send("There is no active game to end.")
            return
        if ctx.author.name != game["host"]:
            await ctx.send("Only the host can end the game!")
            return
        self.games.pop(guild_id)
        await ctx.send(embed=discord.Embed(title="Game Ended", description="The game session has been concluded.", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(Game(bot))
