import asyncio
import logging
import sqlite3
from datetime import UTC, datetime
from statistics import mean

import discord
from discord.ext import commands, tasks

from jack.api import ServiceError
from jack.discord_utils import send_lines
from jack.rendering import render_leaderboard
from jack.stats import player_stats, resolve_metric

log = logging.getLogger(__name__)


def ranked_rows(players, metric: str):
    return sorted(
        ((p["name"], p["stats"][metric]) for p in players),
        key=lambda row: (-row[1], row[0].casefold()),
    )


class Leaderboards(commands.Cog):
    """Bedwars, Skywars, and Duels guild leaderboards."""

    def __init__(self, bot):
        self.bot = bot
        self.refresh_lock = asyncio.Lock()

    async def cog_load(self):
        if not self.bot.offline and self.bot.settings.hypixel_key and self.bot.settings.guild_name:
            self.refresh.start()

    async def cog_unload(self):
        task = self.refresh.get_task()
        self.refresh.cancel()
        if task:
            try:
                await task
            except asyncio.CancelledError:
                pass

    @property
    def cache_key(self):
        return "leaderboard:" + self.bot.settings.guild_name.casefold()

    async def refresh_snapshot(self):
        async with self.refresh_lock:
            guild = await self.bot.api.guild(name=self.bot.settings.guild_name)
            if guild is None:
                raise ServiceError("The configured Hypixel guild was not found.")
            players = []
            for member in guild.get("members", []):
                player = await self.bot.api.player(member["uuid"])
                players.append(
                    {"name": player.get("displayname", "Unknown"), "stats": player_stats(player)}
                )
            # Publish only a complete snapshot; a failed scan keeps the last good one.
            snapshot = {"players": players, "updated": datetime.now(UTC).isoformat()}
            await self.bot.store.put(self.cache_key, snapshot)
            return snapshot

    @tasks.loop(hours=2)
    async def refresh(self):
        try:
            await self.refresh_snapshot()
        except (ServiceError, OSError, sqlite3.Error) as error:
            log.warning(
                "Leaderboard refresh failed (%s); retaining previous snapshot.",
                type(error).__name__,
            )

    @refresh.before_loop
    async def wait_for_ready(self):
        await self.bot.wait_until_ready()

    async def snapshot(self):
        snapshot = await self.bot.store.get(self.cache_key)
        if snapshot is None:
            if self.refresh_lock.locked():
                raise ServiceError(
                    "The first leaderboard is being collected. Please try again shortly."
                )
            snapshot = await self.refresh_snapshot()
        return snapshot

    @commands.command(name="lb")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def leaderboard(
        self, ctx, game: str | None = None, stat: str | None = None, scope: str | None = None
    ):
        """Show a top-ten card: lb bw star. Add 'all' for the complete list."""
        if game is None:
            await ctx.send(
                f"Try `{ctx.clean_prefix}lb bw star`, `lb sw kdr`, or `lb duels wins all`.\nBedwars: star, fkdr, index, wins, finals, wlr. Skywars: star, kills, wins, kdr. Duels: wins, kills, wlr, kdr, bridge_wins."
            )
            return
        try:
            metric = resolve_metric(game, stat)
        except ValueError as error:
            raise commands.BadArgument(str(error)) from None
        if scope is not None and scope.lower() not in ("all", "a"):
            raise commands.BadArgument(
                "Use 'all' for a complete list, or omit it for a top-ten card."
            )
        async with ctx.typing():
            snapshot = await self.snapshot()
            rows = ranked_rows(snapshot["players"], metric.key)
            if scope:
                await send_lines(
                    ctx,
                    metric.title,
                    [
                        f"{i}. **{discord.utils.escape_markdown(name)}**: {value:,.2f}"
                        for i, (name, value) in enumerate(rows, 1)
                    ],
                )
            else:
                card = await asyncio.to_thread(render_leaderboard, metric.title, rows)
                await ctx.send(file=discord.File(card, filename="leaderboard.png"))
            await ctx.send(f"Snapshot: {snapshot['updated']}")

    @commands.command(name="avg", aliases=["a", "average"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def average(self, ctx, game: str = "bw", stat: str | None = None):
        """Show the arithmetic mean of a guild stat: avg bw fkdr."""
        try:
            metric = resolve_metric(game, stat)
        except ValueError as error:
            raise commands.BadArgument(str(error)) from None
        snapshot = await self.snapshot()
        values = [p["stats"][metric.key] for p in snapshot["players"]]
        description = f"{mean(values):,.2f}" if values else "No players yet."
        embed = discord.Embed(title=f"Average {metric.title}", description=description)
        embed.set_footer(text=f"Snapshot: {snapshot['updated']}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Leaderboards(bot))
