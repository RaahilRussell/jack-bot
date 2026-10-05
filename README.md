# Jack

Jack is a Discord companion for Hypixel guilds that handles Minecraft account verification, applications, game-stat leaderboards, moderation, guild activity reports, and community utilities. Originally built as an early programming project, it was restored and modernized into a tested, maintainable Python application while keeping its Minecraft character and playful commands.

## Highlights

- Asynchronous Hypixel/Mojang REST integration with a shared HTTP session, bounded requests, and paced Hypixel calls.
- Pillow-generated Bedwars, Skywars, and Duels leaderboard cards using the original Minecraft map backgrounds.
- SQLite persistence for application records and complete guild-stat snapshots, with database work off the event loop.
- Account verification against Hypixel-linked Discord usernames and private application channels tracked across restarts.
- Permission-aware moderation, role hierarchy checks, scoped channel deletion, and credentials supplied through environment configuration.
- Offline behavioral tests, Ruff and mypy checks, and GitHub Actions CI across Python 3.11–3.14.

## Demo / Screenshots

Screenshots will be added after a live test-server run. The [capture guide](docs/screenshots/README.md) describes the leaderboard, application, and verification views to include and how to keep them anonymous.

<!-- Add only reviewed, anonymized captures of actual bot output here, with descriptive alt text. -->

## Features

- **Hypixel & Minecraft:** profile lookups, linked Discord accounts, Bedwars void deaths, and eligibility checks.
- **Guild management:** weekly activity reports, member requirement reports, and manual invitation logging.
- **Applications & verification:** automatic eligibility checks, private staff review, waiting lists, and configured membership roles.
- **Leaderboards:** top-ten image cards, full rankings, and averages for Bedwars, Skywars, Duels, and Bridge wins.
- **Moderation:** timed mutes, role-based indefinite mutes, kicks, bans, unbans, and role inspection.
- **Community & utilities:** staff-approved quotes, animal images, ping, Mango, and optional channel-scoped deleted-message retrieval.

## Architecture

Discord commands live in six cogs. They call shared services for HTTP, calculations, storage, and rendering; configuration stays outside command logic.

```text
jack/
  bot.py          bot lifecycle, shared HTTP session, extension loading
  cogs/           commands and Discord event listeners
  api.py          Mojang/Hypixel requests and upstream error handling
  stats.py        game formulas, eligibility rules, metric aliases
  storage.py      SQLite application records and guild snapshots
  rendering.py    leaderboard images using Pillow
  config.py       environment-based settings
```

Extensions load once in `setup_hook`, and background jobs and the HTTP session close with the bot. SQLite operations and image rendering run through `asyncio.to_thread`. Guild scans publish only complete snapshots, so a failed refresh retains the last good result with its timestamp. Application records are keyed by channel instead of a shared “current applicant.”

## Tech Stack

| Area | Technologies |
| --- | --- |
| Runtime & Discord | Python 3.11+, discord.py 2.x, asyncio |
| APIs, state & images | aiohttp, SQLite, Pillow |
| Quality | pytest, pytest-asyncio, Ruff, mypy |
| Tooling & CI | uv, GitHub Actions |

## Getting Started

Install Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from the repository directory:

```sh
uv sync --locked
cp .env.example .env
uv run python -m jack --check
```

The startup check loads all command groups without credentials or network requests. To connect, set `DISCORD_TOKEN` in `.env`; add `HYPIXEL_API_KEY` and `HYPIXEL_GUILD` for guild features. Enable Discord's **Message Content** and **Server Members** intents and configure the bot's permissions using the [setup guide](docs/setup.md).

```sh
uv run python -m jack
```

## Commands

Start with `j!help`, `j!check MinecraftName`, or `j!lb bw star`. The prefix is configurable.

The [complete command reference](docs/commands.md) covers arguments, aliases, permissions, cooldowns, and leaderboard metrics.

## Background / Restoration

The restoration preserves the original bot's guild workflows, prefix commands, game formulas, and Minecraft imagery. The focus was making an early project reliable, understandable, and maintainable while removing private configuration and identity-specific behavior. Historical contributors and asset creators remain acknowledged in [CREDITS.md](CREDITS.md).

## Modernization

The major changes are a modern discord.py runtime, shared async HTTP, SQLite replacing external database assumptions, reusable stat/rendering logic, persistent applications, safer permissions and moderation, environment-based configuration, privacy cleanup, and automated tests and CI.

See the [migration notes](docs/modernization.md) for behavioral differences and the [verification record](docs/verification.md) for checks and remaining live-test limits.

## Development

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run python -m jack --check
uv build
```

Tests use local fixtures and mocks; they do not send Discord messages or require API credentials. A real test server is still needed to validate live permissions and account linking.
