# Jack

A Discord companion for a Hypixel guild: Minecraft account verification, guild applications, game-stat leaderboards, moderation, and a few deliberately silly commands. Built with Python and discord.py.

## Background

This project is a restored and modernized version of an early programming project. The implementation has been cleaned up while preserving its guild-focused commands, Minecraft leaderboard cards, and playful personality.

## Features

- Bedwars, Skywars, Duels, and Bridge leaderboards, with top-ten image cards and full text lists.
- Guild stat averages, application eligibility checks, and member activity reports.
- Private application channels, persistent applicant tracking, acceptance, and invitation logging.
- Verification against the Discord username linked on a Hypixel profile.
- Timed mutes, kicks, bans, unbans, and role inspection.
- Staff-approved quote submissions, animal images, Mango, and a latency check.

## Getting Started

Install Python **3.11 or newer** and [uv](https://docs.astral.sh/uv/getting-started/installation/). From this repository's directory:

```sh
uv sync --locked
cp .env.example .env
```

Edit `.env` and set `DISCORD_TOKEN` to a Discord **bot** token. For Hypixel features, also set `HYPIXEL_API_KEY` and `HYPIXEL_GUILD`. Obtain the key from the [Hypixel developer dashboard](https://developer.hypixel.net/). Never commit `.env`.

In the [Discord developer portal](https://discord.com/developers/applications), enable **Message Content Intent** and **Server Members Intent**, then invite the bot to your server with the `bot` scope. No slash-command registration is required.

Grant View Channels, Send Messages, Embed Links, Attach Files, Read Message History, and Add Reactions. Features that need more permissions are listed below; Administrator is unnecessary.

| Feature | Additional bot permissions / setup |
| --- | --- |
| Verification | Manage Roles, Manage Nicknames; `Member`, `Guest`, and optional `Unverified` roles |
| Applications | Manage Channels, Manage Roles; `Staff`, `Accepted`, and `#invite-waiting-list` |
| Invitation log | `#invite-log` |
| Quote review | Manage Messages; `#quote-book-submissions` and `#quote-book` |
| Moderation | Moderate Members, Kick Members, Ban Members as appropriate |
| Indefinite mute | Manage Roles and a `Muted` role with channel overrides denying sending/speaking |

Place Jack's role above roles it assigns and members it moderates. Staff moderation commands require the matching Discord moderation permission. Application and invitation commands accept the configured `Staff` role or Manage Server; quote review accepts that role or Manage Messages. Presence changes and the bounded `spam` command are bot-owner-only.

Role and channel names can be changed in `.env`. Optional `GUILD_RANK_ROLES` maps in-game ranks to Discord role names, for example `GUILD_RANK_ROLES={"Veteran":"Veteran"}`. Only map roles you intend verification to assign; no staff ranks are mapped by default.

## Running

Check that all command groups load without logging in or making network requests:

```sh
uv run python -m jack --check
```

Run the bot:

```sh
uv run python -m jack
```

`uv run jack-bot` and `uv run python main.py` are equivalent entry points. Keep the process running on your host; there is no embedded web server or artificial keep-alive service.

The default prefix is `j!`. Set `COMMAND_PREFIX` to change it.

```text
j!help
j!check MinecraftName
j!requirements
j!apply MinecraftName
j!verify MinecraftName
j!lb bw star
j!lb duels bridge_wins all
j!avg sw kdr
j!inactive
j!gamereqs
j!mute @member 10m a reason
j!unmute @member
j!mango
```

Use `accept`, `deny`, or `deletechannel` inside a recorded application channel. `invited MinecraftName` records a manual invite; it does not send an in-game invitation. `discord MinecraftName` reads the profile's publicly linked Discord username; `void MinecraftName` counts Bedwars void deaths.

Mango always replies with “Mango...”. To add videos, place your own `.mp4` or `.mov` files in the ignored `media/` directory. Old personal clips are not bundled. `snipe` is opt-in through `ENABLE_SNIPE=true`; it exposes the last deleted text message only in its original channel for five minutes. Restarting clears that in-memory cache.

## Project Structure

```text
jack/
  bot.py             startup, lifecycle, and embedded help
  config.py          environment settings
  api.py             asynchronous Minecraft/Hypixel HTTP requests
  stats.py           game formulas and metric aliases
  storage.py         local SQLite state
  rendering.py       image leaderboard cards
  cogs/              community, fun, moderation, Hypixel, leaderboards, errors
  assets/            original clean map backgrounds and font
tests/               offline behavioral tests
```

## Technical Notes

- One shared HTTP session, request timeouts, and paced Hypixel calls keep the Discord event loop responsive. Hypixel uses its [v2 API](https://api.hypixel.net/) with the key in an HTTP header.
- Complete guild snapshots refresh every two hours. A failed refresh retains the previous snapshot; responses display its timestamp. The first scan can take several minutes for a large guild. Server downtime does not expire saved snapshots.
- SQLite state lives in `data/jack.sqlite3`. Keep `data/` on persistent storage for applications and cached leaderboards; run one Jack process per data directory. No MongoDB server is needed.
- Timed mutes use Discord timeouts, which survive restarts and expire automatically. Omitting the duration applies the configured `Muted` role; Discord role/channel overrides determine its effect, and other roles may override a denial. Existing roles are never stripped.
- The original application rule is index ≥ 2,000, or index ≥ 1,000 plus 3,000 Duels wins and 2 WLR. The original existing-member report intentionally has lower thresholds. `requirements` explains both. Index is stars × FKDR²; zero-denominator ratios retain the original value of zero.
- Verification compares the Hypixel-linked Discord username, not a display name. It is not an OAuth account-linking service. Applications are staff recruitment tools; `apply` does not prove ownership of the supplied Minecraft account.

## Modernization

Duplicate leaderboard code now shares one calculation and rendering path. Application state is scoped to its channel and survives restarts. Network failures produce useful messages, missing roles are validated, channel deletion is limited to recorded applications, and moderation respects hierarchy. Generated screenshots, old personal metadata, bytecode, unused dependencies, and the obsolete web keep-alive service have been removed.

The restoration keeps prefix commands and the simple cog architecture. See [migration notes](docs/modernization.md) for deliberate behavior changes and [credits](CREDITS.md) for retained third-party attribution. The original repository supplied no project-wide license; this restoration does not invent one.

## Development

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run python -m jack --check
uv build
```

The tests use local fixtures and mocks, with no credentials or Discord messages. Live guild permissions and API credentials still need a test-server check before deployment.
