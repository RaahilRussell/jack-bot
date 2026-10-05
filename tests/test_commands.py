from dataclasses import dataclass, field
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from jack.cogs.community import Community
from jack.cogs.hypixel import Hypixel
from jack.cogs.moderation import Moderation, check_hierarchy, parse_duration
from jack.config import Settings
from jack.discord_utils import send_lines
from jack.storage import Store


@dataclass(order=True, frozen=True)
class Role:
    position: int
    name: str = field(compare=False, default="Role")
    managed: bool = field(compare=False, default=False)

    def is_default(self):
        return self.position == 0


def context():
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.author.id = 1
    ctx.author.top_role = Role(50)
    ctx.guild.id = 100
    ctx.guild.owner_id = 99
    ctx.guild.me.id = 2
    ctx.guild.me.top_role = Role(100)
    ctx.guild.me.guild_permissions = discord.Permissions.all()
    ctx.guild.roles = [
        Role(0, "@everyone"),
        Role(5, "Muted"),
        Role(10, "Accepted"),
        Role(20, "Staff"),
    ]
    ctx.guild.default_role = ctx.guild.roles[0]
    ctx.guild.name = "Example server"
    ctx.channel.id = 200
    ctx.channel.delete = AsyncMock()
    ctx.bot.settings = Settings()
    return ctx


def target():
    member = MagicMock()
    member.id = 3
    member.top_role = Role(10)
    member.roles = [Role(0), Role(10)]
    for method in ["send", "kick", "ban", "timeout", "edit", "add_roles", "remove_roles"]:
        setattr(member, method, AsyncMock())
    member.display_name = "Example member"
    return member


@pytest.mark.parametrize(
    ("value", "seconds"), [("30s", 30), ("10m", 600), ("2H", 7200), ("28d", 2419200)]
)
def test_duration(value, seconds):
    assert parse_duration(value).total_seconds() == seconds


@pytest.mark.parametrize("value", ["", "0m", "-1h", "2", "3weeks", "29d", "0.5h"])
def test_bad_duration(value):
    with pytest.raises(commands.BadArgument):
        parse_duration(value)


@pytest.mark.parametrize("member_id", [1, 2, 99])
def test_cannot_moderate_self_bot_or_owner(member_id):
    ctx, member = context(), target()
    member.id = member_id
    with pytest.raises(commands.BadArgument):
        check_hierarchy(ctx, member)


def test_both_role_hierarchies_enforced():
    ctx, member = context(), target()
    member.top_role = Role(50)
    with pytest.raises(commands.BadArgument, match="below your"):
        check_hierarchy(ctx, member)
    ctx.author.id = ctx.guild.owner_id
    member.top_role = Role(100)
    with pytest.raises(commands.BadArgument, match="Jack's role"):
        check_hierarchy(ctx, member)


async def test_timed_mute_does_not_strip_roles_or_wait():
    ctx, member = context(), target()
    cog = Moderation(ctx.bot)
    await cog.mute.callback(cog, ctx, member, "10m", reason="Example")
    member.timeout.assert_awaited_once_with(timedelta(minutes=10), reason="Example")
    member.edit.assert_not_awaited()
    member.remove_roles.assert_not_awaited()


async def test_indefinite_mute_only_adds_configured_role():
    ctx, member = context(), target()
    cog = Moderation(ctx.bot)
    await cog.mute.callback(cog, ctx, member)
    member.add_roles.assert_awaited_once_with(ctx.guild.roles[1], reason="No reason supplied")
    member.edit.assert_not_awaited()
    member.remove_roles.assert_not_awaited()


async def test_closed_dms_do_not_prevent_kick():
    ctx, member = context(), target()
    member.send.side_effect = discord.Forbidden(
        SimpleNamespace(status=403, reason="Forbidden"), "DM disabled"
    )
    cog = Moderation(ctx.bot)
    await cog.kick.callback(cog, ctx, member, reason="A multi-word reason")
    member.kick.assert_awaited_once_with(reason="A multi-word reason")
    ctx.send.assert_awaited()


async def test_unmute_preserves_unrelated_roles():
    ctx, member = context(), target()
    member.roles.append(ctx.guild.roles[1])
    cog = Moderation(ctx.bot)
    await cog.unmute.callback(cog, ctx, member)
    member.remove_roles.assert_awaited_once_with(ctx.guild.roles[1], reason="Unmuted by staff")
    member.timeout.assert_awaited_once_with(None, reason="Unmuted by staff")
    member.edit.assert_not_awaited()


async def test_unban_by_id_uses_no_ban_list():
    ctx = context()
    ctx.guild.unban = AsyncMock()
    cog = Moderation(ctx.bot)
    await cog.unban.callback(cog, ctx, member="123")
    assert ctx.guild.unban.call_args.args[0].id == 123
    ctx.guild.bans.assert_not_called()


async def test_application_lookup_is_channel_and_guild_scoped(tmp_path):
    ctx = context()
    ctx.bot.store = Store(tmp_path / "state.sqlite3")
    cog = Hypixel(ctx.bot)
    await ctx.bot.store.put("application:200", {"guild_id": 100, "user_id": 11})
    await ctx.bot.store.put("application:201", {"guild_id": 100, "user_id": 22})
    assert (await cog.application(ctx))["user_id"] == 11
    ctx.channel.id = 201
    assert (await cog.application(ctx))["user_id"] == 22
    ctx.guild.id = 999
    with pytest.raises(commands.BadArgument):
        await cog.application(ctx)


async def test_delete_rejects_unrecorded_channels(tmp_path):
    ctx = context()
    ctx.bot.store = Store(tmp_path / "state.sqlite3")
    cog = Hypixel(ctx.bot)
    with pytest.raises(commands.BadArgument, match="only works inside"):
        await cog.delete_channel.callback(cog, ctx)
    ctx.channel.delete.assert_not_awaited()


async def test_apply_creates_private_overwrites_and_persists(tmp_path):
    ctx = context()
    ctx.bot.store = Store(tmp_path / "state.sqlite3")
    ctx.bot.api.guild = AsyncMock(return_value=None)
    channel = MagicMock()
    channel.id = 300
    channel.mention = "#application-example"
    channel.send = AsyncMock()
    ctx.guild.create_text_channel = AsyncMock(return_value=channel)
    cog = Hypixel(ctx.bot)
    cog.player_named = AsyncMock(return_value=({"id": "example-id", "name": "Example"}, {}))
    await cog.apply.callback(cog, ctx, "Example")
    overwrites = ctx.guild.create_text_channel.call_args.kwargs["overwrites"]
    assert overwrites[ctx.guild.default_role].view_channel is False
    assert overwrites[ctx.author].view_channel is True
    assert overwrites[ctx.guild.me].view_channel is True
    record = await ctx.bot.store.get("application:300")
    assert record["user_id"] == 1
    assert await ctx.bot.store.get("applicant:100:1") == 300


async def test_repeated_application_does_not_create_another(tmp_path):
    ctx = context()
    ctx.bot.store = Store(tmp_path / "state.sqlite3")
    await ctx.bot.store.put("applicant:100:1", 300)
    ctx.guild.fetch_channel = AsyncMock(return_value=MagicMock())
    cog = Hypixel(ctx.bot)
    with pytest.raises(commands.BadArgument, match="already"):
        await cog.apply.callback(cog, ctx, "Example")
    ctx.guild.create_text_channel.assert_not_called()


async def test_accept_uses_saved_applicant_after_reopen(tmp_path, monkeypatch):
    ctx = context()
    store = Store(tmp_path / "state.sqlite3")
    await store.put("application:200", {"guild_id": 100, "user_id": 22, "ign": "Example"})
    ctx.bot.store = Store(store.path)
    ctx.bot.api.profile = AsyncMock(return_value={"id": "example", "name": "Example"})
    ctx.bot.api.guild = AsyncMock(return_value=None)
    member = target()
    member.id = 22
    ctx.guild.get_member.return_value = member
    cog = Hypixel(ctx.bot)
    cog.add_to_waiting_list = AsyncMock()
    monkeypatch.setattr("jack.cogs.hypixel.asyncio.sleep", AsyncMock())
    await cog.accept.callback(cog, ctx)
    assert cog.add_to_waiting_list.call_args.args[1].id == 22
    ctx.channel.delete.assert_awaited_once()
    assert await store.get("application:200") is None


async def test_mismatched_verification_grants_nothing():
    ctx = context()
    ctx.bot.settings = Settings(guild_name="Example")
    ctx.author.add_roles = AsyncMock()
    cog = Hypixel(ctx.bot)
    cog.player_named = AsyncMock(
        return_value=({"id": "x"}, {"socialMedia": {"links": {"DISCORD": "other-user"}}})
    )
    with pytest.raises(commands.BadArgument, match="Link your current"):
        await cog.verify.callback(cog, ctx, "Example")
    ctx.author.add_roles.assert_not_awaited()


async def test_snipe_never_exposes_another_channel():
    ctx = context()
    ctx.bot.settings = Settings(snipe_enabled=True)
    cog = Community(ctx.bot)
    message = MagicMock()
    message.guild.id = ctx.guild.id
    message.channel.id = 777
    message.author.bot = False
    message.content = "Private channel text"
    await cog.on_message_delete(message)
    await cog.snipe.callback(cog, ctx)
    assert ctx.send.call_args.args == ("There is no recent message to snipe!",)


async def test_long_lists_fit_discord_limits():
    ctx = context()
    await send_lines(ctx, "Leaderboard", ["x" * 100] * 125)
    assert ctx.send.await_count > 1
    assert all(len(call.kwargs["embed"].description) <= 4096 for call in ctx.send.call_args_list)
