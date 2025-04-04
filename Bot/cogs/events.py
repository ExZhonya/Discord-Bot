# /cogs/events.py
import discord
from discord.ext import commands
from db.database import get_channel_id
from db.database import get_autoroles

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        guild_id = guild.id

        # Get autoroles
        role_ids = await get_autoroles(self.bot, member.guild.id)
        roles = [member.guild.get_role(rid) for rid in role_ids]
        roles = [r for r in roles if r is not None]
        try:
            await member.add_roles(*roles)
        except Exception as e:
            print(f"⚠️ Could not assign autoroles to {member.name}: {e}")

        # Send welcome message
        welcome_channel_id = await get_channel_id(self.bot, guild_id, "welcome_channel")
        rules_channel_id = await get_channel_id(self.bot, guild_id, "rules_channel")
        roles_channel_id = await get_channel_id(self.bot, guild_id, "role_channel")
        introduction_channel_id = await get_channel_id(self.bot, guild_id, "introduction_channel")

        if welcome_channel_id:
            welcome_channel = self.bot.get_channel(welcome_channel_id)
            if welcome_channel:
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
                                f"{intro_text}\n\n"
                                f"**Start having fun!** 🎉\n\n",
                    color=discord.Color.green()
                )
                embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Enjoy your stay! If you have any questions, feel free to ask. | Today at {current_time}")

                await welcome_channel.send(embed=embed)

        if rules_channel_id:
            rules_channel = self.bot.get_channel(rules_channel_id)
            if rules_channel:
                msg = await rules_channel.send(f"📜 {member.mention}, please read the rules!")
                await msg.delete(delay=1)


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = guild.system_channel
        if channel is None:
            for c in guild.text_channels:
                if c.permissions_for(guild.me).send_messages:
                    channel = c
                    break

        if channel:
            embed = discord.Embed(
                description=(
                    f"**Thanks for adding me to your server! 🥰**\n\n"
                    "Yuuki is an multi-purpose bot, that can assist you in moderation, in managing server, and more!\n\n"
                    "Want to see all of my command list? Then just do `.help` to see all of my available commands!\n\n"
                    "If you have any questions, suggestion and/or need assistance, feel free to join our [support server](https://discord.gg/Tfug7jMMRv)\n\n"
                ),
                color=discord.Color.pink()
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(text="\nThanks for choosing Yuuki!", icon_url=self.bot.user.avatar.url)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Events(bot))
