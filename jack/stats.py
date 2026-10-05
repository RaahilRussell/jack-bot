"""Game formulas from the original bot, shared by commands and leaderboards."""

from dataclasses import dataclass
from typing import Any

GUILD_XP = (
    100_000,
    150_000,
    250_000,
    500_000,
    750_000,
    1_000_000,
    1_250_000,
    1_500_000,
    2_000_000,
    2_500_000,
    2_500_000,
    2_500_000,
    2_500_000,
    2_500_000,
    3_000_000,
)
SKYWARS_XP = (0, 20, 70, 150, 250, 500, 1000, 2000, 3500, 6000, 10000, 15000)
WEEKLY_GEXP = 100_000


def ratio(numerator: float, denominator: float) -> float:
    # Preserve the original convention for an unplayed/zero-death mode.
    return round(numerator / denominator, 2) if denominator else 0.0


def guild_level(experience: float) -> float:
    remaining = max(0, experience)
    for level, required in enumerate(GUILD_XP):
        if remaining < required:
            return level + remaining / required
        remaining -= required
    return min(1000, len(GUILD_XP) + remaining / GUILD_XP[-1])


def skywars_level(experience: float) -> float:
    experience = max(0, experience)
    for level in range(1, len(SKYWARS_XP)):
        lower, upper = SKYWARS_XP[level - 1 : level + 1]
        if experience < upper:
            return level + (experience - lower) / (upper - lower)
    return 12 + (experience - SKYWARS_XP[-1]) / 10000


def player_stats(player: dict[str, Any]) -> dict[str, float]:
    stats = player.get("stats") or {}
    bw, sw, duels = (stats.get(game) or {} for game in ("Bedwars", "SkyWars", "Duels"))
    stars = (player.get("achievements") or {}).get("bedwars_level", 0)
    fkdr = ratio(bw.get("final_kills_bedwars", 0), bw.get("final_deaths_bedwars", 0))
    return {
        "bw.star": stars,
        "bw.fkdr": fkdr,
        "bw.index": int(stars * fkdr**2),
        "bw.wins": bw.get("wins_bedwars", 0),
        "bw.finals": bw.get("final_kills_bedwars", 0),
        "bw.wlr": ratio(bw.get("wins_bedwars", 0), bw.get("losses_bedwars", 0)),
        "sw.star": skywars_level(sw.get("skywars_experience", 0)),
        "sw.kills": sw.get("kills", 0),
        "sw.wins": sw.get("wins", 0),
        "sw.kdr": ratio(sw.get("kills", 0), sw.get("deaths", 0)),
        "duels.wins": duels.get("wins", 0),
        "duels.kills": duels.get("kills", 0),
        "duels.wlr": ratio(duels.get("wins", 0), duels.get("losses", 0)),
        "duels.kdr": ratio(duels.get("kills", 0), duels.get("deaths", 0)),
        "duels.bridge_wins": duels.get("bridge_duel_wins", 0),
    }


def meets_requirements(stats: dict[str, float]) -> bool:
    """Original application/check rule; the old README-style embed disagreed."""
    return stats["bw.index"] >= 2000 or (
        stats["bw.index"] >= 1000 and stats["duels.wins"] >= 3000 and stats["duels.wlr"] >= 2
    )


def meets_retention_requirements(stats: dict[str, float]) -> bool:
    """The original gamereqs command used a separate, lower member threshold."""
    return (
        stats["bw.star"] >= 150
        and stats["bw.fkdr"] >= 1
        and (
            stats["bw.index"] >= 1000
            or (
                stats["bw.index"] >= 650 and stats["duels.wins"] >= 1000 and stats["duels.wlr"] >= 1
            )
        )
    )


@dataclass(frozen=True)
class Metric:
    key: str
    title: str


GAME_NAMES = {"bw": "Bedwars", "sw": "Skywars", "duels": "Duels"}
METRICS = {
    f"{game}.{stat}": Metric(f"{game}.{stat}", f"{GAME_NAMES[game]} {label}")
    for game, entries in {
        "bw": {
            "star": "Stars",
            "fkdr": "FKDR",
            "index": "Index",
            "wins": "Wins",
            "finals": "Finals",
            "wlr": "WLR",
        },
        "sw": {"star": "Stars", "kills": "Kills", "wins": "Wins", "kdr": "KDR"},
        "duels": {
            "wins": "Wins",
            "kills": "Kills",
            "wlr": "WLR",
            "kdr": "KDR",
            "bridge_wins": "Bridge Wins",
        },
    }.items()
    for stat, label in entries.items()
}


def resolve_metric(game: str, stat: str | None = None) -> Metric:
    game = {
        "b": "bw",
        "bedwars": "bw",
        "s": "sw",
        "skywars": "sw",
        "d": "duels",
        "duel": "duels",
    }.get(game.lower(), game.lower())
    stat = (stat or ("wins" if game == "duels" else "star")).lower()
    stat = {
        "s": "star",
        "stars": "star",
        "fk": "fkdr",
        "fkd": "fkdr",
        "i": "index",
        "f": "finals",
        "final": "finals",
        "w": "wins",
        "win": "wins",
        "wl": "wlr",
        "wlrs": "wlr",
        "k": "kills",
        "kill": "kills",
        "kd": "kdr",
        "bw": "bridge_wins",
        "bridge_win": "bridge_wins",
    }.get(stat, stat)
    try:
        return METRICS[f"{game}.{stat}"]
    except KeyError:
        raise ValueError(
            "Choose bw: star/fkdr/index/wins/finals/wlr; sw: star/kills/wins/kdr; duels: wins/kills/wlr/kdr/bridge_wins."
        ) from None
