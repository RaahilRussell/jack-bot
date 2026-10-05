from unittest.mock import patch

import pytest

from jack.bot import JackBot
from jack.config import Settings


async def test_load_every_extension_and_reconnect_without_network(tmp_path):
    with patch("aiohttp.ClientSession.get", side_effect=AssertionError("Unexpected network")):
        async with JackBot(Settings(data_dir=tmp_path), offline=True) as bot:
            await bot.setup_hook()
            assert len(bot.cogs) == 6
            for command in [
                "help",
                "ping",
                "pingg",
                "mango",
                "snipe",
                "cat",
                "duck",
                "rpanda",
                "penguin",
                "fart",
                "spam",
                "member",
                "mute",
                "unmute",
                "ban",
                "unban",
                "kick",
                "status",
                "discord",
                "void",
                "apply",
                "accept",
                "deny",
                "delete",
                "accepted",
                "verify",
                "inactive",
                "gamereqs",
                "check",
                "invited",
                "requirements",
                "lb",
                "avg",
                "GameReqs",
                "Invite",
            ]:
                assert bot.get_command(command) is not None, command
            await bot.on_ready()
            await bot.on_ready()
            assert len(bot.extensions) == 6
            session = bot.session
        assert session.closed
        assert not bot.extensions
    assert not list(tmp_path.iterdir())


def test_config_never_leaks_credentials_in_repr():
    settings = Settings.from_env(
        {"DISCORD_TOKEN": "private-discord-value", "HYPIXEL_API_KEY": "private-hypixel-value"}
    )
    assert "private-" not in repr(settings)
    assert settings.prefix == "j!"


@pytest.mark.parametrize("value", ["", "x" * 11])
def test_invalid_prefix(value):
    with pytest.raises(ValueError):
        Settings.from_env({"COMMAND_PREFIX": value})


@pytest.mark.parametrize("value", ["[]", "invalid json", '{"Rank":12}'])
def test_invalid_rank_map(value):
    with pytest.raises(ValueError, match="GUILD_RANK_ROLES"):
        Settings.from_env({"GUILD_RANK_ROLES": value})
