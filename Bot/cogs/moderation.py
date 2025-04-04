# /cogs/moderation.py
import discord, time, re, asyncio
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from db.database import get_channel_id, set_channel_id, remove_channel_id, ensure_guild_exists, log_infraction, get_infractions

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# ---------------- Slash Commands ----------------
    @app_commands.command(name="setchannel", description="(Admin) Set moderation or system channels.")
    @app_commands.describe(
        channel_type="Select the type of channel to configure",
        channel="The channel you want to assign"
    )
    @app_commands.choices(channel_type=[
        app_commands.Choice(name="Welcome", value="welcome"),
        app_commands.Choice(name="Rules", value="rules"),
        app_commands.Choice(name="Heartbeat", value="heartbeat"),
        app_commands.Choice(name="Role", value="role"),
        app_commands.Choice(name="Introduction", value="introduction"),
        app_commands.Choice(name="Mod Log", value="log"),
        app_commands.Choice(name="Infractions List", value="list")
    ])
    async def setchannel_slash(self, interaction: discord.Interaction, 
                            channel_type: app_commands.Choice[str], 
                            channel: discord.TextChannel):

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need manage server permissions!", ephemeral=True)
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


# ---------------- Text Commands ----------------
    @commands.command()
    async def setchannel(self, ctx, channel_type: str, *, channel: discord.TextChannel, channel_or_value: str):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("❌ You need manage server permissions!", delete_after=3)
            return

        if channel_type.lower() not in ["welcome", "rules", "heartbeat", "role", "introduction", "log", "list"]:
            await ctx.send("❌ Invalid type! Use `welcome`, `rules`, `heartbeat`, `role`, `introduction`, `log`, or `list`.", delete_after=3)
            return

        channel_type = "role" if channel_type.lower() in ["role", "roles"] else channel_type.lower()
        column_name = f"{channel_type.lower()}_channel"
        guild_id = ctx.guild.id
        await ensure_guild_exists(self.bot, guild_id)
        
        """For Community's onboard function Channel&Roles"""
        if channel_or_value.lower() == "community":
            await set_channel_id(self.bot, guild_id, column_name, "community")
            await ctx.send(f"✅ {channel_type.capitalize()} channel set to community mode (`<id:customize>`).")
            return
        """For Error Catch"""
        try:
            channel = await commands.TextChannelConverter().convert(ctx, channel_or_value)
        except commands.BadArgument:
            await ctx.send("❌ Invalid channel. Please mention a valid text channel or use `community`.", delete_after=3)
            return

        current_channel_id = await get_channel_id(self.bot, guild_id, column_name)
        if current_channel_id == channel.id:
            await remove_channel_id(self.bot, guild_id, column_name)
            await ctx.send(f"✅ {channel_type.capitalize()} has been removed from {channel.mention}.")
        else:
            await set_channel_id(self.bot, guild_id, column_name, channel.id)
            await ctx.send(f"✅ {channel_type.capitalize()} channel set to {channel.mention}!")

    @commands.command()
    async def say(ctx, *, message: str):
        embed = discord.Embed(
            description=message,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def welcomepreview(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("You need the 'Manage Server' permission to use this command!", delete_after = 5)
            return

        guild = ctx.guild
        guild_id = guild.id
        member = ctx.author

        welcome_channel_id = await get_channel_id(self.bot, guild_id, "welcome_channel")
        rules_channel_id = await get_channel_id(self.bot, guild_id, "rules_channel")
        roles_channel_id = await get_channel_id(self.bot, guild_id, "role_channel")
        introduction_channel_id = await get_channel_id(self.bot, guild_id, "introduction_channel")

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


    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, *args):
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("❌ You need the `Manage Messages` permission to use this command.", delete_after=5)
            return
        
        if len(args) == 0:
            await ctx.send("❌ Usage: `.purge [@member] <amount>`", delete_after=5)
            return


        if len(args) == 1:
            try:
                limit = int(args[0])
            except ValueError:
                await ctx.send("❌ Please provide a valid number of messages to purge.", delete_after=5)
                return
            member = None

        else:
            try:
                member = await commands.MemberConverter().convert(ctx, args[0])
                limit = int(args[1])
            except (commands.BadArgument, ValueError):
                await ctx.send("❌ Usage: `.purge [@member] <amount>`", delete_after=5)
                return

        if limit > 100:
            await ctx.send("❌ You can only purge up to 100 messages at a time.", delete_after=5)
            return

        def check(m):
            return m.author == member if member else True

        deleted = await ctx.channel.purge(limit=limit, check=check)
        if member:
            await ctx.send(f"✅ Deleted {len(deleted)} messages from {member.mention}.", delete_after=5)
        else:
            await ctx.send(f"✅ Deleted {len(deleted)} messages.", delete_after=5)


    # Utility for time parsing
    def parse_time(self, time_str):
        time_units = {"m": 60, "h": 3600, "d": 86400, "mo": 2592000, "y": 31536000}
        pattern = r"(\\d+)([a-zA-Z]+)"
        matches = re.findall(pattern, time_str)
        total_seconds = 0
        for value, unit in matches:
            unit = unit.lower()
            if unit in time_units:
                total_seconds += int(value) * time_units[unit]
        return total_seconds

    # Centralized log function
    async def mod_log(self, ctx, action: str, member: discord.Member, reason: str, duration: str = None):
        guild_id = ctx.guild.id
        log_channel_id = await get_channel_id(self.bot, guild_id, "log_channel")
        list_channel_id = await get_channel_id(self.bot, guild_id, "list_channel")

        # ✅ DB logging here
        await log_infraction(self.bot, guild_id, member.id, ctx.author.id, action, reason, int(time.time()))

        # Mod Log Text
        if log_channel_id:
            log_channel = ctx.guild.get_channel(log_channel_id)
            await log_channel.send(f"{action} | {member} | by {ctx.author} | Reason: {reason}")

        # Infractions Embed
        if list_channel_id:
            now = int(time.time())
            list_channel = ctx.guild.get_channel(list_channel_id)
            embed = discord.Embed(
                title=f"Infraction: {action} User",
                color=discord.Color.red() if action in ["Banned", "Muted"] else discord.Color.orange()
            )
            embed.add_field(name="User", value=f"{member} | {member.mention}", inline=False)
            embed.add_field(name="Mod", value=f"{ctx.author} | {ctx.author.mention}", inline=False)
            embed.add_field(name="Duration", value=f"<t:{now}:F>{f' | Expires: {duration}' if duration else ''}", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            await list_channel.send(embed=embed)


    # MUTE Command
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason="No reason provided"):
        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name="Muted")

        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            for channel in guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False, add_reactions=False)

        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f"🔇 {member.mention} has been muted for {duration or 'indefinitely'}. Reason: {reason}")

        await self.mod_log(ctx, "Muted", member, reason, duration)

        # Auto unmute if timed
        if duration:
            seconds = self.parse_time(duration)
            await asyncio.sleep(seconds)
            if muted_role in member.roles:
                await member.remove_roles(muted_role)
                await ctx.send(f"🔊 {member.mention} has been automatically unmuted.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f"🔊 {member.mention} has been unmuted.")
        else:
            await ctx.send(f"{member.mention} is not muted.")

    # KICK Command
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason}")
        await self.mod_log(ctx, "Kicked", member, reason)

    # BAN Command
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.ban(reason=reason)
        await ctx.send(f"⛔ {member.mention} has been banned. Reason: {reason}")
        await self.mod_log(ctx, "Banned", member, reason)

    # WARN Command
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await ctx.send(f"⚠️ {member.mention} has been warned. Reason: {reason}")
        await self.mod_log(ctx, "Warned", member, reason)

    @commands.command(name="infraction")
    async def infraction(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.send("❌ You need the `Manage Members` permission to use this command.", delete_after=5)
            return

        records = await get_infractions(self.bot, ctx.guild.id, member.id)
        if not records:
            await ctx.send(f"No infractions found for {member}.")
            return

        pages = [records[i:i+5] for i in range(0, len(records), 5)]

        class InfractionView(View):
            def __init__(self):
                super().__init__()
                self.page = 0

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
            async def previous(self, interaction: discord.Interaction, button: Button):
                if self.page > 0:
                    self.page -= 1
                    await interaction.response.edit_message(embed=make_embed(self.page))

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
            async def next(self, interaction: discord.Interaction, button: Button):
                if self.page < len(pages) - 1:
                    self.page += 1
                    await interaction.response.edit_message(embed=make_embed(self.page))

        def make_embed(page):
            embed = discord.Embed(
                title=f"Infractions for {member} (Page {page+1}/{len(pages)})",
                color=discord.Color.blurple()
            )
            for idx, inf in enumerate(pages[page], start=1):
                embed.add_field(
                    name=f"{idx}. {inf['action']}",
                    value=f"Reason: {inf['reason']} | Mod: <@{inf['mod_id']}> | Date: <t:{inf['timestamp']}:F>",
                    inline=False
                )
            return embed

        await ctx.send(embed=make_embed(0), view=InfractionView())

    @commands.command(name="clearinfractions")
    @commands.has_permissions(manage_guild=True)
    async def clearinfractions(self, ctx, member: discord.Member):
        await self.bot.db.execute("""
            DELETE FROM infractions WHERE guild_id = $1 AND user_id = $2
        """, ctx.guild.id, member.id)

        await ctx.send(f"✅ Cleared all infractions for {member}.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
