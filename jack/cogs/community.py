import asyncio
import random
import time
from collections import OrderedDict

import discord
from discord.ext import commands

from jack.discord_utils import require_channel


class Community(commands.Cog):
    """Quotes, utility commands, and Mango."""

    def __init__(self, bot):
        self.bot = bot
        self.deleted = OrderedDict()
        self.quote_lock = asyncio.Lock()

    @commands.command(aliases=["pingg"])
    async def ping(self, ctx):
        """Show Discord gateway and message latency."""
        start = time.perf_counter()
        message = await ctx.send("Testing ping...")
        elapsed = (time.perf_counter() - start) * 1000
        await message.edit(content=f"Pong! {self.bot.latency * 1000:.0f}ms\nAPI: {elapsed:.0f}ms")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mango(self, ctx):
        """Mango. Optional local videos live in MEDIA_DIR."""
        await ctx.send("Mango...")
        paths = [
            p
            for p in self.bot.settings.media_dir.glob("*")
            if p.suffix.lower() in (".mp4", ".mov") and p.is_file()
        ]
        limit = ctx.guild.filesize_limit if ctx.guild else 10 * 1024 * 1024
        paths = [p for p in paths if p.stat().st_size <= limit]
        if paths:
            await ctx.send(file=discord.File(random.choice(paths), filename="mango.mp4"))

    @commands.command()
    @commands.is_owner()
    async def status(self, ctx, *, text: str):
        """Change Jack's presence (bot owner only)."""
        if len(text) > 128:
            raise commands.BadArgument("Keep the status to 128 characters or fewer.")
        await self.bot.change_presence(activity=discord.Game(name=text))
        await ctx.send("Status updated.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, name=self.bot.settings.unverified_role)
        if role is not None and role < member.guild.me.top_role and not role.managed:
            await member.add_roles(role, reason="Awaiting verification")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not self.bot.settings.snipe_enabled or not message.guild or message.author.bot:
            return
        key = (message.guild.id, message.channel.id)
        self.deleted[key] = (time.monotonic(), str(message.author), message.content[:3900])
        self.deleted.move_to_end(key)
        while len(self.deleted) > 100:
            self.deleted.popitem(last=False)

    @commands.command()
    @commands.guild_only()
    async def snipe(self, ctx):
        """Show the last deleted message in this channel, if enabled (five-minute window)."""
        if not self.bot.settings.snipe_enabled:
            await ctx.send(
                "Snipe is disabled. The server operator can opt in with ENABLE_SNIPE=true."
            )
            return
        key = (ctx.guild.id, ctx.channel.id)
        entry = self.deleted.get(key)
        if entry is None or time.monotonic() - entry[0] > 300:
            self.deleted.pop(key, None)
            await ctx.send("There is no recent message to snipe!")
            return
        await ctx.send(
            embed=discord.Embed(
                title=f"Message from {entry[1]}", description=entry[2] or "[No text]"
            )
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            message.guild
            and not message.author.bot
            and message.channel.name == self.bot.settings.quote_submissions
        ):
            await message.add_reaction("✅")
            await message.add_reaction("❌")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        member = payload.member
        if not payload.guild_id or member is None or member.bot:
            return
        channel = member.guild.get_channel(payload.channel_id)
        if channel is None or channel.name != self.bot.settings.quote_submissions:
            return
        permitted = member.guild_permissions.manage_messages or any(
            role.name == self.bot.settings.staff_role for role in member.roles
        )
        if not permitted or str(payload.emoji) not in ("✅", "❌"):
            return
        # Serialize approvals so two staff reactions cannot repost the same quote.
        async with self.quote_lock:
            try:
                message = await channel.fetch_message(payload.message_id)
                if message.author.bot:
                    return
                if str(payload.emoji) == "✅":
                    destination = require_channel(member.guild, self.bot.settings.quote_channel)
                    content = "\n".join([message.content] + [a.url for a in message.attachments])
                    for start in range(0, len(content), 1900):
                        await destination.send(
                            content[start : start + 1900],
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                await message.delete()
            except discord.NotFound:
                return


async def setup(bot):
    await bot.add_cog(Community(bot))
