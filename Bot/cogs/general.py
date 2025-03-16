# /cogs/general.py
import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"🏓 Pong! Latency: {round(self.bot.latency * 1000)}ms")

    @commands.command()
    async def info(self, ctx):
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

    @commands.command()
    async def help(self, ctx):
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

    @commands.command()
    async def gamehelp(self, ctx):
        embed = discord.Embed(
            title="Game Help",
            color=discord.Color.blue()
        )
        embed.add_field(name=".game <type>", value="Use this to start a game. Public | Private", inline=False)
        embed.add_field(name=".start", value="Start the game.", inline=False)
        embed.add_field(name=".endgame", value="Use this to end an existing game.", inline=False)
        embed.add_field(name=".menu", value="Open the Game's Menu.", inline=False)
        embed.add_field(name=".addgold <@user> <value>", value="Add a player's gold.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def channelhelp(self, ctx):
        embed = discord.Embed(
            title="Set Channel Help",
            color=discord.Color.blue()
        )
        embed.add_field(name=".setchannel <type> <channel>", value="Set your channel.", inline=False)
        embed.add_field(name=".setchannel welcome", value="Set your welcome channel.", inline=False)
        embed.add_field(name=".setchannel rules", value="Set your rules channel.", inline=False)
        embed.add_field(name=".setchannel heartbeat", value="Set a heartbeat message of the bot's status.", inline=False)
        embed.add_field(name=".setchannel role", value="Set your role selection channel.", inline=False)
        embed.add_field(name=".setchannel introduction", value="Set your introduction channel.", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
