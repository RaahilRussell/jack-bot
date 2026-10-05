from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from PIL import Image

from jack.api import ServiceError
from jack.cogs.leaderboards import Leaderboards, ranked_rows
from jack.config import Settings
from jack.rendering import render_leaderboard
from jack.stats import METRICS, player_stats
from jack.storage import Store


async def test_state_survives_reopen_and_delete(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    await store.put("application:10", {"user_id": 1})
    await store.put("application:20", {"user_id": 2})
    reopened = Store(store.path)
    assert await reopened.get("application:10") == {"user_id": 1}
    assert await reopened.get("application:20") == {"user_id": 2}
    await reopened.put("application:10", {"user_id": 3})
    assert await store.get("application:10") == {"user_id": 3}
    await store.delete("application:10")
    assert await reopened.get("application:10") is None


async def test_snapshot_preserves_previous_data_on_api_failure(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    bot = SimpleNamespace(
        settings=Settings(guild_name="Example"),
        store=store,
        api=SimpleNamespace(
            guild=AsyncMock(return_value={"members": [{"uuid": "a"}, {"uuid": "b"}]}),
            player=AsyncMock(side_effect=[{"displayname": "First"}, ServiceError("rate limited")]),
        ),
    )
    cog = Leaderboards(bot)
    previous = {"players": [{"name": "Previous", "stats": player_stats({})}], "updated": "old"}
    await store.put(cog.cache_key, previous)
    with pytest.raises(ServiceError):
        await cog.refresh_snapshot()
    assert await cog.snapshot() == previous


async def test_empty_snapshot_and_fractional_average(tmp_path):
    bot = SimpleNamespace(
        settings=Settings(guild_name="Example"),
        store=Store(tmp_path / "state.sqlite3"),
        api=SimpleNamespace(guild=AsyncMock(return_value={"members": []})),
    )
    cog = Leaderboards(bot)
    assert (await cog.refresh_snapshot())["players"] == []
    ctx = SimpleNamespace(send=AsyncMock())
    await cog.average.callback(cog, ctx, "duels", "bridge_wins")
    assert ctx.send.call_args.kwargs["embed"].description == "No players yet."
    await bot.store.put(
        cog.cache_key,
        {
            "players": [
                {"name": "A", "stats": {"duels.kdr": 1}},
                {"name": "B", "stats": {"duels.kdr": 2}},
            ],
            "updated": "now",
        },
    )
    await cog.average.callback(cog, ctx, "duels", "kdr")
    assert ctx.send.call_args.kwargs["embed"].description == "1.50"


def test_sort_keeps_names_paired_and_breaks_ties():
    players = [
        {"name": "Second", "stats": {"bw.fkdr": 2}},
        {"name": "First", "stats": {"bw.fkdr": 8}},
        {"name": "Another", "stats": {"bw.fkdr": 8}},
    ]
    assert ranked_rows(players, "bw.fkdr") == [("Another", 8), ("First", 8), ("Second", 2)]


@pytest.mark.parametrize("count", [0, 1, 9, 10, 15])
def test_render_small_or_large_guild(count):
    result = render_leaderboard("Bedwars Stars", [("Player", 100.5)] * count)
    with Image.open(result) as image:
        assert image.size == (1000, 1000)
        assert image.format == "PNG"


@pytest.mark.parametrize("metric", METRICS.values(), ids=lambda m: m.key)
def test_every_card_can_render(metric):
    with Image.open(render_leaderboard(metric.title, [("Example_Player", 1234)])) as image:
        image.verify()
