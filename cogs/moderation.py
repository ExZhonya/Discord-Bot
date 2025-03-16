# /cogs/moderation.py
import discord
from discord.ext import commands
from discord import app_commands
from db.database import get_channel_id, set_channel_id, remove_channel_id, ensure_guild_exists

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash Command for /setchannel
    @app_commands.command(name="setchannel", description="(Admin) Set welcome, rules, heartbeat, role, or introduction channel.")
    @app_commands.describe(
        channel_type="Select the type of channel to configure",
        channel="The channel you want to assign"
    )
    @app_commands.choices(channel_type=[
        app_commands.Choice(name="Welcome", value="welcome"),
        app_commands.Choice(name="Rules", value="rules"),
        app_commands.Choice(name="Heartbeat", value="heartbeat"),
        app_commands.Choice(name="Role", value="role"),
        app_commands.Choice(name="Introduction", value="introduction")
    ])
    async def setchannel_slash(self, interaction: discord.Interaction, 
                               channel_type: app_commands.Choice[str], 
                               channel: discord.TextChannel):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need admin permissions!", ephemeral=True)
            return

        guild_id = interaction.guild.id
        column_name = f"{channel_type.value}_channel"
        await ensure_guild_exists(self.bot, guild_id)

        current_channel_id = await get_channel_id(self.bot, guild_id, column_name)
        if current_channel_id == channel.id:
            await remove_channel_id(self.bot, guild_id, column_name)
            await interaction.response.send_message(f"✅ `{channel_type.name}` has been **removed** from {channel.mention}.", ephemeral=False)
        else:
            await set_channel_id(self.bot, guild_id, column_name, channel.id)
            await interaction.response.send_message(f"✅ `{channel_type.name}` set to {channel.mention}!", ephemeral=False)

    # Legacy dot command version
    @commands.command()
    async def setchannel(self, ctx, channel_type: str, channel: discord.TextChannel):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You need admin permissions!", delete_after=3)
            return

        if channel_type.lower() not in ["welcome", "rules", "heartbeat", "role", "introduction"]:
            await ctx.send("❌ Invalid type! Use `welcome`, `rules`, or `heartbeat`.", delete_after=3)
            return

        column_name = f"{channel_type.lower()}_channel"
        guild_id = ctx.guild.id
        await ensure_guild_exists(self.bot, guild_id)

        current_channel_id = await get_channel_id(self.bot, guild_id, column_name)
        if current_channel_id == channel.id:
            await remove_channel_id(self.bot, guild_id, column_name)
            await ctx.send(f"✅ {channel_type.capitalize()} has been removed from {channel.mention}.")
        else:
            await set_channel_id(self.bot, guild_id, column_name, channel.id)
            await ctx.send(f"✅ {channel_type.capitalize()} channel set to {channel.mention}!")

    @commands.command()
    async def rules(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("You need the 'Manage Server' permission to use this command!")
            return

        rules_channel_id = await get_channel_id(self.bot, ctx.guild.id, "rules_channel")
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
            await ctx.message.delete(delay=5)
            await msg.delete(delay=5)

    @commands.command()
    async def welcomepreview(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("You need the 'Manage Server' permission to use this command!")
            return

        guild = ctx.guild
        guild_id = guild.id
        member = ctx.author

        welcome_channel_id = await get_channel_id(self.bot, guild_id, "welcome_channel")
        rules_channel_id = await get_channel_id(self.bot, guild_id, "rules_channel")
        roles_channel_id = await get_channel_id(self.bot, guild_id, "role_channel")
        introduction_channel_id = await get_channel_id(self.bot, guild_id, "introduction_channel")

        if not welcome_channel_id:
            await ctx.send("⚠️ No welcome channel is set! Use `.setchannel welcome #channel` first.")
            return

        current_time = discord.utils.utcnow().strftime("%I:%M %p")
        rules_text = f"<a:exclamation:1350752095720177684> Read the rules in <#{rules_channel_id}>" if rules_channel_id else "<a:exclamation:1350752095720177684> Read the rules in the rules channel."
        roles_text = f"<a:exclamation:1350752095720177684> Get yourself a role on <#{roles_channel_id}>" if roles_channel_id else "<a:exclamation:1350752095720177684> Get yourself a role in the roles channel."
        intro_text = f"<a:exclamation:1350752095720177684> Introduce yourself in <#{introduction_channel_id}>" if introduction_channel_id else "<a:exclamation:1350752095720177684> Introduce yourself in the introduction channel."

        embed = discord.Embed(
            title=f"👋 Welcome, {member.name}!",
            description=f"We're excited to see you here!\n\n"
                        f"`Welcome to {guild.name}`\n\n"
                        f"{rules_text}\n\n"
                        f"{roles_text}\n\n"
                        f"{intro_text}\n\n",
            color=discord.Color.green()
        )

        embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Enjoy your stay! If you have any questions, feel free to ask. | Today at {current_time}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
