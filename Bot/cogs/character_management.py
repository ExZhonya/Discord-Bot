# Refactored updates based on your requests

import discord
from discord.ext import commands
from utils.views import continue_game_logic

AVAILABLE_CLASSES = ["warrior", "archer", "mage", "priest"]

class CharacterManagement(commands.Cog):
    def __init__(self, bot, game_manager):
        self.bot = bot
        self.game_manager = game_manager

    @commands.command()
    async def continue_game(self, ctx):
        guild_id = ctx.guild.id
        game = self.game_manager.get_game(guild_id)
        if not game["active"] or not game.get("has_started"):
            await ctx.send("No active game stage to continue.")
            return
        await continue_game_logic(ctx, game)

    @commands.command()
    async def addstats(self, ctx, member: discord.Member = None, stat: str = None, amount: int = None):
        guild_id = ctx.guild.id
        game = self.game_manager.get_game(guild_id)
        caller = ctx.author

        if game["visibility"] == "public" and not caller.guild_permissions.administrator:
            return await ctx.send("❌ Only admins can add stats in public games.")
        if game["visibility"] == "private" and caller.name != game["host"]:
            return await ctx.send("❌ Only the GM can add stats in private games.")

        if not member or not stat or amount is None:
            return await ctx.send("Usage: `.addstats @user stat amount`.")

        player_data = game["team_data"].get(member.name)
        if not player_data:
            print("All stored players:", game["team_data"].keys())  # Check stored usernames
            print("Target player name:", member.name)  # Check how Discord sees the username

            return await ctx.send("❌ Player not found in game.")

        if player_data["stats"]["StatPoints"] < amount:
            return await ctx.send("❌ Not enough available stat points.")

        if stat.capitalize() not in ["Str", "Int", "Def", "Dex"]:
            return await ctx.send("❌ Invalid stat type.")

        player_data["stats"][stat.capitalize()] += amount
        player_data["stats"]["StatPoints"] -= amount

        await ctx.send(f"✅ Added {amount} {stat.capitalize()} to {member.name}.")

    @commands.command()
    async def setclass(self, ctx, member: discord.Member = None, class_name: str = None):
        guild_id = ctx.guild.id
        game = self.game_manager.get_game(guild_id)
        caller = ctx.author

        if game["visibility"] == "public" and not caller.guild_permissions.administrator:
            return await ctx.send("❌ Only admins can set classes in public games.")
        if game["visibility"] == "private" and caller.name != game["host"]:
            return await ctx.send("❌ Only the GM can set classes in private games.")

        if not member or not class_name:
            return await ctx.send("Usage: `.setclass @user class_name`.")

        if class_name.lower() not in AVAILABLE_CLASSES:
            return await ctx.send(f"❌ Invalid class. Available classes: {', '.join(AVAILABLE_CLASSES)}")

        player_data = game["team_data"].get(member.name)
        if not player_data:
            return await ctx.send("❌ Player not found in game.")

        player_data["class"] = class_name.lower()
        await ctx.send(f"✅ {member.name} is now a **{class_name.capitalize()}**!")

async def setup(bot):
    from cogs.game import Game  # import your game manager
    await bot.add_cog(CharacterManagement(bot, Game(bot)))
