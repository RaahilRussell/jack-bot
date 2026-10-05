import pytest

from jack.stats import (
    METRICS,
    guild_level,
    meets_requirements,
    meets_retention_requirements,
    player_stats,
    ratio,
    resolve_metric,
    skywars_level,
)


def test_sparse_player_has_every_metric():
    stats = player_stats({})
    assert set(stats) == set(METRICS)
    assert stats["sw.star"] == 1
    assert all(value == 0 for key, value in stats.items() if key != "sw.star")
    assert player_stats({"stats": None, "achievements": None}) == stats


def test_actual_game_keys_and_squared_index():
    stats = player_stats(
        {
            "achievements": {"bedwars_level": 200},
            "stats": {
                "Bedwars": {
                    "final_kills_bedwars": 300,
                    "final_deaths_bedwars": 100,
                    "wins_bedwars": 125,
                    "losses_bedwars": 50,
                },
                "SkyWars": {"skywars_experience": 25000, "kills": 30, "deaths": 20, "wins": 5},
                "Duels": {
                    "wins": 3500,
                    "losses": 1000,
                    "kills": 120,
                    "deaths": 40,
                    "bridge_duel_wins": 42,
                },
            },
        }
    )
    assert stats["bw.index"] == 1800
    assert stats["bw.wlr"] == 2.5
    assert stats["sw.star"] == 13
    assert stats["sw.kdr"] == 1.5
    assert stats["duels.bridge_wins"] == 42
    assert stats["duels.kdr"] == 3
    assert meets_requirements(stats)


@pytest.mark.parametrize(
    ("index", "wins", "wlr", "expected"),
    [
        (2000, 0, 0, True),
        (1999, 0, 0, False),
        (1000, 3000, 2, True),
        (999, 3000, 2, False),
        (1000, 2999, 2, False),
        (1000, 3000, 1.99, False),
    ],
)
def test_application_boundaries(index, wins, wlr, expected):
    assert meets_requirements({"bw.index": index, "duels.wins": wins, "duels.wlr": wlr}) is expected


def test_retention_rule_stays_distinct():
    stats = {"bw.star": 150, "bw.fkdr": 2.1, "bw.index": 661, "duels.wins": 1000, "duels.wlr": 1}
    assert meets_retention_requirements(stats)
    assert not meets_requirements(stats)
    assert not meets_retention_requirements({**stats, "bw.star": 149})


@pytest.mark.parametrize(("xp", "level"), [(0, 1), (20, 2), (10, 1.5), (15000, 12), (25000, 13)])
def test_skywars_thresholds(xp, level):
    assert skywars_level(xp) == level


def test_guild_level_and_zero_death_convention():
    assert guild_level(0) == 0
    assert guild_level(100000) == 1
    assert guild_level(175000) == 1.5
    assert guild_level(10**12) == 1000
    assert ratio(12, 0) == 0
    assert ratio(1, 3) == 0.33


@pytest.mark.parametrize(
    ("game", "stat", "key"),
    [
        ("B", "fk", "bw.fkdr"),
        ("sw", None, "sw.star"),
        ("duel", "bw", "duels.bridge_wins"),
        ("duels", None, "duels.wins"),
        ("d", "kd", "duels.kdr"),
        ("bw", "f", "bw.finals"),
    ],
)
def test_legacy_metric_aliases(game, stat, key):
    assert resolve_metric(game, stat).key == key


def test_unknown_metric_fails_helpfully():
    with pytest.raises(ValueError, match="Choose bw"):
        resolve_metric("unknown")
