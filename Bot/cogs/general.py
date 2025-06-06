# /cogs/general.py
import discord, random, asyncio, time, re
from discord.ext import commands
from discord.ui import View, Button
from discord import TextChannel
from discord.utils import utcnow, format_dt

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bully_surdi_active = False
        self.surdi_user_id = 609342457301303308

    @commands.command()
    async def bully(self, ctx, target: str = None, toggle: str = None):
        excluded_user_id = 609342457301303308

        if ctx.author.id == excluded_user_id:
            await ctx.send("idih ngapain sur")
            return
    
        if target and target.lower() == "surdi":
            if toggle and toggle.lower() == "on":
                self.bully_surdi_active = True
                await ctx.send("👀 Bully Surdi is now **ON**.")
            elif toggle and toggle.lower() == "off":
                self.bully_surdi_active = False
                await ctx.send("😇 Bully Surdi is now **OFF**.")
            else:
                await ctx.send("❓ Use `.bully surdi on` or `.bully surdi off`")
        else:
            await ctx.send("❓ Use `.bully surdi on` or `.bully surdi off`")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.bully_surdi_active:
            for user in message.mentions:
                if user.id == self.surdi_user_id:
                    await message.channel.send("sst gausah ping. surdi itu gay, kriminal wanita, narsis pula, mending jauh jauh deh")
                    break




    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"🏓 \n Pong! Latency: `{round(self.bot.latency * 1000)}`ms")

    @commands.command()
    async def serverinfo(self, ctx):
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
        embed.add_field(name=".serverinfo", value="Provides server information.", inline=False)
        embed.add_field(name=".gamehelp", value="List of Game's commands.", inline=False)
        embed.add_field(name=".modhelp", value="List of admin's commands help.", inline=False)
        embed.add_field(name=".giveaway", value="To create a Giveaway.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def modhelp(self, ctx):
        embed = discord.Embed(
            title="Mod Help",
            color=discord.Color.blue()
        )
        embed.add_field(name=".channelhelp", value="(Admin) Set welcome, rules, or heartbeat channels.", inline=False)
        embed.add_field(name=".infraction", value="To see Member's list of infractions.", inline=False)
        embed.add_field(name=".clearinfractions", value="To clear member's infractions.", inline=False)
        embed.add_field(name=".mute", value="To mute a member.", inline=False)
        embed.add_field(name=".kick", value="To kick a member.", inline=False)
        embed.add_field(name=".ban", value="To ban a member.", inline=False)
        embed.add_field(name=".ar <add/remove/list>", value="To add, remove or see autorole list ", inline=False)
        embed.add_field(name=".say", value="To send a message using Bot's embed feature.", inline=False)
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
        embed.add_field(name=".setchannel list", value="Set your member infractions.", inline=False)
        await ctx.send(embed=embed)


    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author  # fallback to author if no member mentioned

        embed = discord.Embed(
            title=f"🖼️ Avatar for {member.display_name}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")

        await ctx.send(embed=embed)

    def parse_time(self, timestr: str) -> int:
        """Parses time like 1h30m into seconds"""
        time_units = {"m": 60, "h": 3600, "d": 86400, "mo": 2592000, "y": 31536000}
        pattern = r"(\d+)([a-zA-Z]+)"
        matches = re.findall(pattern, timestr)
        total_seconds = 0
        for value, unit in matches:
            unit = unit.lower()
            if unit in time_units:
                total_seconds += int(value) * time_units[unit]
        return total_seconds

    class GiveawayView(View):
        def __init__(self, timeout):
            super().__init__(timeout=timeout)
            self.participants = set()

        @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.green)
        async def join_button(self, interaction: discord.Interaction, button: Button):
            if interaction.user.id not in self.participants:
                self.participants.add(interaction.user.id)
                await interaction.response.send_message("✅ You've joined the giveaway!", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ You already joined!", ephemeral=True)

    @commands.group()
    @commands.has_permissions(manage_messages=True)
    async def giveaway(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("❌ Usage: `.giveaway create <#channel> <winners> <duration> <prize>`")

    @giveaway.command()
    async def create(self, ctx, channel: TextChannel, winners: int, duration: str, *, prize: str):
        total_seconds = self.parse_time(duration)
        if total_seconds < 30:
            await ctx.send("❌ Duration must be at least 30 seconds.")
            return

        now = utcnow()
        end_timestamp = int((now.timestamp()) + total_seconds)

        embed = discord.Embed(
            title="🎉 New Giveaway!",
            description=(
                f"**Prize:** {prize}\n"
                f"**Winners:** {winners}\n"
                f"**Hosted by:** {ctx.author.mention}\n"
                f"**Time Remaining:** <t:{end_timestamp}:R>\n"
                f"**Ends at:** <t:{end_timestamp}:t>"
            ),
            color=discord.Color.gold()
        )

        view = self.GiveawayView(timeout=total_seconds)
        await channel.send(embed=embed, view=view)
        await ctx.send(f"✅ Giveaway started in {channel.mention} for **{prize}**!")

        await asyncio.sleep(total_seconds)
        view.stop()

        if view.participants:
            winner_ids = random.sample(list(view.participants), min(winners, len(view.participants)))
            winner_mentions = ", ".join(ctx.guild.get_member(w).mention for w in winner_ids if ctx.guild.get_member(w))
            await channel.send(f"🎉 Congratulations {winner_mentions}! You won **{prize}**!")
        else:
            await channel.send("No one joined the giveaway 😢.")

    @commands.command()
    async def roll(self, ctx, dice: str):
        if dice.startswith('d') and dice[1:].isdigit():
            max_num = int(dice[1:])
            if max_num > 0:
                result = random.randint(1, max_num)
                await ctx.send(f'🎲 {ctx.author.mention} You rolled **{result}**!')
            else:
                await ctx.send('❌ Please use a number greater than 0!')
        else:
            await ctx.send('❌ Invalid format! Use `.roll d<number>`')


async def setup(bot):
    await bot.add_cog(General(bot))
