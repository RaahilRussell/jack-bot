# Jack

Jack is a Discord-based management and analytics bot for a competitive gaming community on [Hypixel](https://support.hypixel.net/hc/en-us/articles/360019495360-How-to-Join-the-Hypixel-Server), a large multiplayer Minecraft server. A Hypixel **guild** is a persistent team or community of players. Members compete in different games and use Discord for conversations, recruitment, and administration.

Hypixel exposes player statistics, account information, and guild membership through an API, but staff make membership decisions in Discord. Staff otherwise have to look up applicants, compare statistics, identify inactive members, and update Discord roles manually.

Jack brings those records into Discord. Players verify accounts and apply to join; staff review applications, inspect rankings and activity reports, and moderate from chat. Application state persists across restarts, and collected statistics become rankings and generated leaderboard images.

## What Jack does

### Player verification

Minecraft and Discord accounts have separate usernames. To verify, a player adds their Discord username to their Hypixel profile and gives Jack their Minecraft name. Jack retrieves the profile and compares its linked Discord username with the person running the command.

Discord roles provide membership labels and permissions. After a match, Jack assigns member or guest roles based on guild membership, applies configured rank roles, and attempts a nickname update.

### Applications and membership

An applicant supplies a Minecraft username. Jack looks up their competitive statistics and checks the guild's admission thresholds. Eligible applicants receive an Accepted role and are added to a waiting list. Applicants below the thresholds get a private channel where staff can review their statistics and current guild membership before deciding.

Each review channel has a SQLite record identifying its applicant, so staff can accept or deny the correct application after a restart. Channels are private from creation, duplicate open applications are rejected, and closing commands only affect recorded applications. Invitation logs record the issuing staff member and the applicant’s eligibility. Sending the actual in-game invitation remains a staff action.

### Competitive statistics and leaderboards

Jack ranks guild members across Bedwars, Skywars, and Duels, different competitive games within Hypixel. Rankings include wins, player eliminations, experience levels, and performance ratios.

A win/loss ratio compares victories with defeats. A kill/death ratio compares opponents eliminated with the player's own deaths. Bedwars also distinguishes **final** eliminations, after which a player cannot return to that match; **FKDR** is final kills divided by final deaths. “Stars” represent a game's experience level. Jack combines Bedwars stars and FKDR into an admission score called an index: `stars × FKDR²`.

Rankings can be returned as a full text list or a top-ten card generated with Pillow over Minecraft map artwork. The same stat calculations feed the rankings, averages, and eligibility checks, keeping those results consistent.

### Guild activity

Guild experience measures a player's contribution through gameplay. Jack reports members below the weekly experience threshold and the percentage of the guild they represent. A separate report identifies members below the competitive requirements for existing members; those thresholds differ from admission requirements.

Guild averages summarize each supported competitive statistic. Leaderboards, averages, and the member-requirement report use saved snapshots and display when the data was collected. Reports inform staff decisions without automatically removing members.

### Moderation and community tools

Staff can issue timed mutes, indefinite role-based mutes, kicks, bans, and unbans. Commands check Discord permissions and role hierarchy, and timed mutes use Discord timeouts that expire without keeping the bot running.

Community tools include reaction-based quote approval, animal images, a latency check, and Mango's optional video replies. Deleted-message retrieval is disabled by default; when enabled, it exposes only the latest cached deleted text in the same channel within a five-minute window.

## How it works

Jack is an asynchronous Discord application built with discord.py. Commands and event listeners live in **cogs**, discord.py's command-group modules. Mojang's API resolves Minecraft names to account identifiers; Hypixel's API provides player and guild data.

```text
jack/
  bot.py          startup, extension loading, shared resources
  cogs/           Discord commands and event listeners
  api.py          HTTP requests and service error handling
  stats.py        calculations, eligibility rules, metric aliases
  storage.py      SQLite application records and stat snapshots
  rendering.py    Pillow leaderboard cards
  config.py       environment-based settings
  assets/         map backgrounds and font
tests/            offline behavioral tests
```

This separation keeps Discord interactions apart from calculations and storage. API calls share an aiohttp session with request timeouts and paced Hypixel requests. SQLite operations and image rendering run in worker threads, keeping that work off the event loop while the bot handles other commands.

A background job saves complete guild snapshots every two hours. Failed refreshes leave the previous snapshot available. SQLite stores snapshots and application records locally. Background tasks and the HTTP session close during shutdown.

## Built with

- **Application:** Python 3.11+, discord.py, asyncio, aiohttp
- **Storage and images:** SQLite, Pillow
- **Development:** pytest, Ruff, mypy, uv, GitHub Actions

## Running Jack

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.11+, then run from the repository directory:

```sh
uv sync --locked
cp .env.example .env
uv run python -m jack --check
```

The check loads all command groups without connecting to Discord. Set `DISCORD_TOKEN`, `HYPIXEL_API_KEY`, and `HYPIXEL_GUILD` in `.env`, then follow [server setup](docs/setup.md) for Discord intents, roles, permissions, and persistent storage.

```sh
uv run python -m jack
```

## Commands

The default prefix is `j!`. Replace `MinecraftName` with a player's username.

| Command | Purpose |
| --- | --- |
| `j!verify MinecraftName` | Match a linked account and update Discord membership roles. |
| `j!apply MinecraftName` | Check admission eligibility and start the application workflow. |
| `j!lb bw wins` | Rank guild members by Bedwars wins and generate a leaderboard card. |
| `j!avg duels wlr` | Show the guild's average Duels win/loss ratio. |
| `j!inactive` | Report members below the weekly activity threshold. |
| `j!help` | Show available command groups and usage. |

The [command reference](docs/commands.md) covers arguments, aliases, permissions, and cooldowns.

## Development

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run python -m jack --check
uv build
```

Tests cover calculations, API failures, permissions, application isolation, persistence, rendering, and startup without external credentials. GitHub Actions runs checks on Python 3.11–3.14. Actual role assignment and authenticated integrations still need the [live test-server checks](docs/setup.md#live-smoke-test-checklist).

Contributors and asset attribution are listed in [CREDITS.md](CREDITS.md).
