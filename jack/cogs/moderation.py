import asyncio
import re
from datetime import timedelta

import discord
from discord.ext import commands

from jack.discord_utils import require_role

MAX_TIMEOUT = 28 * 24 * 60 * 60


def parse_duration(value: str) -> timedelta:
    match = re.fullmatch(r"([1-9]\d*)([smhd])", value.lower())
    if match is None:
        raise commands.BadArgument("Use a positive duration such as 30s, 10m, 2h or 7d.")
    seconds = int(match[1]) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[match[2]]
    if seconds > MAX_TIMEOUT:
        raise commands.BadArgument("Discord timeouts cannot exceed 28 days.")
    return timedelta(seconds=seconds)


def check_hierarchy(ctx, member):
    if member.id in (ctx.author.id, ctx.guild.owner_id, ctx.guild.me.id):
        raise commands.BadArgument("You cannot moderate yourself, Jack, or the server owner.")
    if ctx.author.id != ctx.guild.owner_id and member.top_role >= ctx.author.top_role:
        raise commands.BadArgument("You can only moderate members below your highest role.")
    if member.top_role >= ctx.guild.me.top_role:
        raise commands.BadArgument("Jack's role must be above the member's highest role.")


class Moderation(commands.Cog):
    """Moderation with Discord permissions and role hierarchy checks."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.command(aliases=["tempmute"])
    @commands.has_guild_permissions(moderate_members=True)
    @commands.bot_has_guild_permissions(moderate_members=True)
    async def mute(
        self,
        ctx,
        member: discord.Member,
        duration: str | None = None,
        *,
        reason: str = "No reason supplied",
    ):
        """Mute for a duration; omit duration for a configured Muted role without expiry."""
        check_hierarchy(ctx, member)
        if duration:
            await member.timeout(parse_duration(duration), reason=reason[:512])
            await ctx.send(f"{member.display_name} has been muted for {duration}.")
        else:
            if not ctx.guild.me.guild_permissions.manage_roles:
                raise commands.BotMissingPermissions(["manage_roles"])
            role = require_role(ctx.guild, self.bot.settings.muted_role)
            await member.add_roles(role, reason=reason[:512])
            await ctx.send(
                f"{member.display_name} has been given the Muted role until unmuted. Channel overrides must deny sending/speaking."
            )

    @commands.command()
    @commands.has_guild_permissions(moderate_members=True)
    @commands.bot_has_guild_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Clear a timeout and the configured Muted role without touching other roles."""
        check_hierarchy(ctx, member)
        role = discord.utils.get(ctx.guild.roles, name=self.bot.settings.muted_role)
        if role and role in member.roles:
            if not ctx.guild.me.guild_permissions.manage_roles:
                raise commands.BotMissingPermissions(["manage_roles"])
            require_role(ctx.guild, self.bot.settings.muted_role)
            await member.remove_roles(role, reason="Unmuted by staff")
        await member.timeout(None, reason="Unmuted by staff")
        await ctx.send(f"{member.display_name} has been unmuted.")

    async def remove_member(self, ctx, member, reason, *, ban: bool):
        check_hierarchy(ctx, member)
        action = "banned" if ban else "kicked"
        try:
            await member.send(
                f"You have been {action} from {ctx.guild.name}. Reason: {reason[:1000]}"
            )
        except discord.HTTPException:
            pass  # Closed DMs must not prevent a valid moderation action.
        if ban:
            await member.ban(reason=reason[:512], delete_message_seconds=0)
        else:
            await member.kick(reason=reason[:512])
        await ctx.send(f"{member.display_name} has been {action}.")

    @commands.command()
    @commands.has_guild_permissions(kick_members=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason supplied"):
        """Kick a member, optionally providing a reason."""
        await self.remove_member(ctx, member, reason, ban=False)

    @commands.command()
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason supplied"):
        """Ban a member without deleting message history."""
        await self.remove_member(ctx, member, reason, ban=True)

    @commands.command()
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    async def unban(self, ctx, *, member: str):
        """Unban by Discord user ID, or an exact legacy username#discriminator."""
        if member.isdecimal():
            user = discord.Object(id=int(member))
        else:
            user = None
            async for entry in ctx.guild.bans(limit=None):
                if str(entry.user) == member:
                    user = entry.user
                    break
            if user is None:
                raise commands.BadArgument("No matching ban. Try the Discord user ID.")
        try:
            await ctx.guild.unban(user, reason="Unbanned by staff")
        except discord.NotFound:
            raise commands.BadArgument("That user is not banned.") from None
        await ctx.send("User unbanned.")

    @commands.command()
    async def member(self, ctx, member: discord.Member):
        """List a member's role names."""
        await ctx.send(
            embed=discord.Embed(
                title=member.display_name,
                description=", ".join(r.name for r in member.roles if not r.is_default())[:3900]
                or "No roles.",
            )
        )

    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def spam(self, ctx, member: discord.Member, count: int = 3):
        """The old playful command, bounded to 1–5 messages without notifications."""
        if not 1 <= count <= 5:
            raise commands.BadArgument("Choose 1–5 messages.")
        for _ in range(count):
            await ctx.send(member.mention, allowed_mentions=discord.AllowedMentions.none())
            await asyncio.sleep(1)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
