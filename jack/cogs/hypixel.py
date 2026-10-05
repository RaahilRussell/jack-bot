"""Hypixel lookups, guild applications, and verification."""

import asyncio
from typing import Any

import discord
from discord.ext import commands

from jack.api import ServiceError
from jack.discord_utils import require_channel, require_role, send_lines, staff_only
from jack.stats import WEEKLY_GEXP, meets_requirements, meets_retention_requirements, player_stats


def linked_discord(player):
    value = ((player.get("socialMedia") or {}).get("links") or {}).get("DISCORD", "")
    return value if isinstance(value, str) else ""


class Hypixel(commands.Cog):
    """Minecraft players and guild membership."""

    def __init__(self, bot):
        self.bot = bot

    async def player_named(self, name):
        profile = await self.bot.api.profile(name)
        player = await self.bot.api.player(profile["id"])
        return profile, player

    @commands.command(name="discord")
    async def discord_link(self, ctx, ign: str):
        """Look up the Discord username publicly linked to a Hypixel profile."""
        _, player = await self.player_named(ign)
        await ctx.send(linked_discord(player) or "This player has not linked a Discord account.")

    @commands.command()
    async def void(self, ctx, ign: str):
        """Count a player's Bedwars void deaths."""
        profile, player = await self.player_named(ign)
        count = ((player.get("stats") or {}).get("Bedwars") or {}).get("void_deaths_bedwars", 0)
        embed = discord.Embed(
            title="Not bad", description=f"You've only fallen off {count:,} times! Good job!"
        )
        embed.set_author(name=profile["name"])
        await ctx.send(embed=embed)

    @commands.command(aliases=["ch", "chgq"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def check(self, ctx, ign: str):
        """Check the original application requirements for a player."""
        _, player = await self.player_named(ign)
        await ctx.send(
            "This player makes requirements!"
            if meets_requirements(player_stats(player))
            else "This player does not make requirements!"
        )

    @commands.command(aliases=["r", "reqs"])
    async def requirements(self, ctx):
        """Show application and existing-member thresholds."""
        embed = discord.Embed(
            title="Game Requirements",
            description=(
                "**Applications**\n2,000+ Bedwars index, **or** 1,000+ index with 3,000+ Duels wins and 2+ Duels WLR.\n\n"
                "**Existing-member report (gamereqs)**\n150+ Bedwars stars and 1+ FKDR, plus either 1,000+ index or 650+ index with 1,000+ Duels wins and 1+ WLR.\n\n"
                "INDEX = STARS × FKDR². The inactivity report uses 100,000 weekly guild XP."
            ),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True, manage_channels=True)
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def apply(self, ctx, username: str):
        """Join the waiting list when eligible, or open a private staff application."""
        existing = await self.bot.store.get(f"applicant:{ctx.guild.id}:{ctx.author.id}")
        if existing:
            try:
                await ctx.guild.fetch_channel(existing)
            except discord.NotFound:
                await self.bot.store.delete(f"applicant:{ctx.guild.id}:{ctx.author.id}")
            else:
                raise commands.BadArgument("You already have an open application.")
        profile, player = await self.player_named(username)
        stats = player_stats(player)
        guild = await self.bot.api.guild(player=profile["id"])
        if meets_requirements(stats):
            await self.add_to_waiting_list(ctx.guild, ctx.author, profile["name"], guild)
            await ctx.send("You make the requirements! Added you to the waiting list.")
            return
        staff = require_role(ctx.guild, self.bot.settings.staff_role, editable=False)
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            ctx.author: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, attach_files=True
            ),
            staff: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True,
            ),
        }
        # Permissions are applied during creation, with no public interval.
        channel = await ctx.guild.create_text_channel(
            f"application-{profile['name'].lower()}",
            overwrites=overwrites,
            reason="Guild application",
        )
        record = {
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id,
            "ign": profile["name"],
            "uuid": profile["id"],
        }
        try:
            await self.bot.store.put(f"application:{channel.id}", record)
            await self.bot.store.put(f"applicant:{ctx.guild.id}:{ctx.author.id}", channel.id)
        except Exception:
            await channel.delete(reason="Application persistence failed")
            raise
        member: dict[str, Any] = next(
            (
                m
                for m in (guild or {}).get("members", [])
                if m["uuid"].replace("-", "") == profile["id"].replace("-", "")
            ),
            {},
        )
        weekly = sum(member.get("expHistory", {}).values())
        embed = discord.Embed(
            title="Guild application",
            description=(
                f"Staff can review this application even though the automatic requirements are not met.\n\n"
                f"IGN: {profile['name']}\nBedwars: {stats['bw.star']} stars, {stats['bw.fkdr']} FKDR, {stats['bw.index']} index\n"
                f"Duels: {stats['duels.wins']} wins, {stats['duels.wlr']} WLR\n"
                f"Guild: {(guild or {}).get('name', 'None')}\nWeekly guild XP: {weekly:,}"
            ),
        )
        await channel.send(embed=embed)
        await ctx.send(f"Your application is ready in {channel.mention}.")

    async def add_to_waiting_list(self, guild, member, ign, hypixel_guild):
        role = require_role(guild, self.bot.settings.accepted_role)
        waiting = require_channel(guild, self.bot.settings.waiting_channel)
        await member.add_roles(role, reason="Guild application accepted")
        note = " Please leave your current guild." if hypixel_guild else ""
        await waiting.send(
            f"You have been accepted, {member.mention}.{note}\nIGN: {ign}\nGuild: {(hypixel_guild or {}).get('name', 'None')}"
        )

    async def application(self, ctx):
        record = await self.bot.store.get(f"application:{ctx.channel.id}")
        if not record or record["guild_id"] != ctx.guild.id:
            raise commands.BadArgument(
                "This command only works inside an application channel created by Jack."
            )
        return record

    async def close_application(self, ctx, record):
        await ctx.channel.delete(reason="Guild application closed")
        await self.bot.store.delete(f"application:{ctx.channel.id}")
        await self.bot.store.delete(f"applicant:{ctx.guild.id}:{record['user_id']}")

    @commands.command()
    @staff_only()
    @commands.bot_has_guild_permissions(manage_roles=True, manage_channels=True)
    @commands.max_concurrency(1, commands.BucketType.channel, wait=False)
    async def accept(self, ctx, ign: str | None = None):
        """Accept the applicant associated with this channel, including after a restart."""
        record = await self.application(ctx)
        profile = await self.bot.api.profile(ign or record["ign"])
        guild = await self.bot.api.guild(player=profile["id"])
        member = ctx.guild.get_member(record["user_id"]) or await ctx.guild.fetch_member(
            record["user_id"]
        )
        await self.add_to_waiting_list(ctx.guild, member, profile["name"], guild)
        await ctx.send("Accepted! This application will close in 10 seconds.")
        await asyncio.sleep(10)
        await self.close_application(ctx, record)

    @commands.command()
    @staff_only()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def deny(self, ctx):
        """Deny this application and close its channel after ten seconds."""
        record = await self.application(ctx)
        await ctx.send(
            "Apologies, you have not been accepted. This application will close in 10 seconds."
        )
        await asyncio.sleep(10)
        await self.close_application(ctx, record)

    @commands.command(name="deletechannel", aliases=["dc", "channeldelete", "delete"])
    @staff_only()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def delete_channel(self, ctx):
        """Close only the current, recorded application channel."""
        await self.close_application(ctx, await self.application(ctx))

    @commands.command()
    @staff_only()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def accepted(self, ctx, member: discord.Member):
        """Toggle the configured Accepted role."""
        role = require_role(ctx.guild, self.bot.settings.accepted_role)
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send("Accepted role removed.")
        else:
            await member.add_roles(role)
            await ctx.send("Accepted role added.")

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True, manage_nicknames=True)
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def verify(self, ctx, ign: str):
        """Match the profile's linked Discord username and assign configured membership roles."""
        if not self.bot.settings.guild_name:
            raise ServiceError("Set HYPIXEL_GUILD before using verification.")
        profile, player = await self.player_named(ign)
        if linked_discord(player).casefold() != str(ctx.author).casefold():
            raise commands.BadArgument(
                "Link your current Discord username in your Hypixel social settings, then try again."
            )
        guild = await self.bot.api.guild(player=profile["id"])
        in_guild = bool(
            guild and guild.get("name", "").casefold() == self.bot.settings.guild_name.casefold()
        )
        settings = self.bot.settings
        desired = {settings.member_role if in_guild else settings.guest_role}
        if in_guild:
            membership: dict[str, Any] = next(
                (
                    m
                    for m in guild.get("members", [])
                    if m["uuid"].replace("-", "") == profile["id"].replace("-", "")
                ),
                {},
            )
            rank_role = settings.guild_rank_roles.get(membership.get("rank", ""))
            if rank_role:
                desired.add(rank_role)
        roles_to_add = [require_role(ctx.guild, name) for name in desired]
        managed_names = {
            settings.member_role,
            settings.guest_role,
            settings.unverified_role,
            *settings.guild_rank_roles.values(),
        }
        roles_to_remove = [r for r in ctx.author.roles if r.name in managed_names - desired]
        for role in roles_to_remove:
            require_role(ctx.guild, role.name)
        await ctx.author.add_roles(*roles_to_add, reason="Hypixel verification")
        if roles_to_remove:
            await ctx.author.remove_roles(*roles_to_remove, reason="Hypixel verification")
        try:
            await ctx.author.edit(nick=profile["name"], reason="Hypixel verification")
            note = ""
        except discord.Forbidden:
            note = " Roles updated, but Discord would not let Jack change your nickname."
        await ctx.send(
            f"Verified as {profile['name']}! Assigned {', '.join(sorted(desired))}.{note}"
        )

    @commands.command(aliases=["kicklist", "ia"])
    @staff_only()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def inactive(self, ctx):
        """List members below 100,000 weekly guild XP; never kick automatically."""
        guild = await self.bot.api.guild(name=self.bot.settings.guild_name)
        if guild is None:
            raise ServiceError("The configured guild was not found.")
        members = guild.get("members", [])
        inactive = sorted(
            (m for m in members if sum(m.get("expHistory", {}).values()) < WEEKLY_GEXP),
            key=lambda m: sum(m.get("expHistory", {}).values()),
            reverse=True,
        )
        lines = []
        async with ctx.typing():
            for member in inactive:
                profile = await self.bot.api.json(
                    f"https://sessionserver.mojang.com/session/minecraft/profile/{member['uuid']}"
                )
                lines.append(
                    f"{profile.get('name', 'Unknown')} [{member.get('rank', 'Member')}]: {sum(member.get('expHistory', {}).values()):,}"
                )
        percentage = len(inactive) / len(members) if members else 0
        await send_lines(ctx, f"{percentage:.0%} inactive", lines)

    @commands.command(aliases=["gamerequirements", "gq"])
    @commands.cooldown(1, 3600, commands.BucketType.guild)
    async def gamereqs(self, ctx):
        """List members below the original retention thresholds using the cached guild snapshot."""
        leaderboards = self.bot.get_cog("Leaderboards")
        snapshot = await leaderboards.snapshot()
        lines = [
            p["name"] for p in snapshot["players"] if not meets_retention_requirements(p["stats"])
        ]
        await send_lines(ctx, "Below member requirements", lines)
        await ctx.send(f"Snapshot: {snapshot['updated']}")

    @commands.command(aliases=["log", "invite"])
    @staff_only()
    async def invited(self, ctx, ign: str):
        """Record an invitation; this does not issue an in-game guild invite."""
        channel = require_channel(ctx.guild, self.bot.settings.invite_channel)
        profile, player = await self.player_named(ign)
        verdict = "✅" if meets_requirements(player_stats(player)) else "❌"
        await channel.send(
            f"{profile['name']} was invited by {ctx.author.mention} {verdict}\nThis is a manual invitation log."
        )
        await ctx.send("Invitation logged.")


async def setup(bot):
    await bot.add_cog(Hypixel(bot))
