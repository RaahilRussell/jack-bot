# Jack

Jack is a Discord bot built for running a competitive guild on [Hypixel](https://hypixel.net/), one of Minecraft's largest multiplayer servers.

Hypixel guilds are persistent player communities: members play together, compete across different game modes, earn experience for the guild, and often use a separate Discord server to organize the community. That creates an awkward split between two systems — the game knows who players are and how they perform, while Discord is where applications, staff decisions, roles, rankings, and day-to-day community management happen.

Jack connects the two. It uses Hypixel's player and guild data inside Discord to verify members, handle applications, track activity and performance, maintain leaderboards, and give staff the tools to run the community without constantly switching between profiles, spreadsheets, and manual Discord administration.

## What Jack does

### Player verification

A Discord username by itself does not prove which Minecraft account belongs to that person.

Jack turns Hypixel's public profile linking into a lightweight account-verification system. A player first signs into Hypixel through Minecraft and adds their Discord username to the social links on their Hypixel profile. They then run Jack's verification command with their Minecraft username.

Jack looks up that Minecraft account through the Mojang and Hypixel APIs and checks whether the Discord username published on the Hypixel profile matches the Discord user running the command.

From the player's perspective, the flow is:

```text
Log into Minecraft / Hypixel
        ↓
Link Discord username on Hypixel profile
        ↓
Run j!verify <Minecraft username> in Discord
        ↓
Jack checks the Hypixel profile
        ↓
Published Discord username matches the invoking user
        ↓
Jack assigns the appropriate guild roles
```

Verification rejects a claimed Minecraft account unless its published Discord username matches the invoking user. This relies on the player keeping that profile link current.

Once verified, Jack can distinguish between current guild members and other verified players, assign the configured Discord roles and guild-rank roles, and update the member's nickname to their Minecraft name when permissions allow. Discord roles provide membership labels and control access within the server.

### Applications and membership

For an applicant, Jack turns joining the guild into a Discord workflow instead of a back-and-forth process with staff.

An applicant only needs to provide their Minecraft username:

```text
j!apply PlayerName
```

Jack retrieves their Hypixel profile, calculates the statistics the guild uses for admissions, and checks whether they meet the current entry requirements.

If the player already meets the requirements, Jack can place them directly into the accepted/waiting-list workflow so staff know they are ready for an in-game invitation.

If they fall below the automatic requirements, Jack creates a private application channel for the applicant and guild staff. Staff can then review the player's account and make a manual decision rather than forcing every applicant through the same cutoff.

This gives applicants a much cleaner experience:

- no screenshots of stats
- no manually filling out numbers that staff then have to verify
- no searching through several stat websites
- a private place to discuss an application
- a clear accepted/denied outcome
- persistent application state even if the bot restarts

For staff, Jack also prevents duplicate open review channels, keeps each application tied to the submitting Discord user and supplied Minecraft account, posts accepted applicants to the waiting list, and records invitations. Account verification is a separate command; an application alone does not establish ownership of the supplied account.

The actual in-game guild invite is intentionally left to staff rather than letting the bot control the Minecraft account.

### Competitive statistics and leaderboards

Stats are not only used to decide who gets into the guild. They also give members something to compete over once they are inside it.

Jack collects statistics for every guild member across Bedwars, Skywars, and Duels and turns them into rankings that can be viewed directly in Discord.

For someone unfamiliar with Hypixel, these are separate competitive game modes with their own progression systems and performance statistics. Jack tracks measurements such as:

- wins
- kills (opponents eliminated)
- experience levels
- win/loss ratio (victories divided by defeats)
- kill/death ratio (opponents eliminated divided by the player's own deaths)
- Bedwars final kills and final deaths

In Bedwars, a **final kill** eliminates a player for the remainder of the match. **FKDR** measures final kills per final death and is one of the common indicators of Bedwars performance. Jack can also calculate an index combining experience and performance, where **stars** represent the player's Bedwars experience level:

`Bedwars stars × FKDR²`

Members can request full rankings or top-ten leaderboard cards generated with Pillow over Minecraft map artwork.

The purpose isn't just to display numbers. The leaderboards give members a reason to compete with each other, see where they stand within the guild, and work toward moving up the rankings. That gives the Discord server a recurring competitive element outside of individual matches and helps make guild membership feel more meaningful.

The same centralized stat calculations are reused for leaderboards, guild averages, and membership checks, so the bot does not calculate the same metric differently in different parts of the system.

### Guild monitoring and analytics

A competitive guild has two related questions:

1. **Are members still active?**
2. **How is the current roster performing?**

Hypixel awards **Guild Experience (GEXP)** when members play games. That experience contributes to the guild's overall progression, so guilds commonly use weekly GEXP as a rough indicator of whether members are actively contributing.

Jack collects this information for the entire roster and turns it into staff-facing reports.

The activity report identifies members below the guild's weekly contribution threshold and summarizes how much of the roster falls below it. Instead of manually opening profiles or maintaining a spreadsheet, staff can quickly see which members may have become inactive.

A separate competitive-requirements report compares current members against the guild's ongoing performance expectations. Admission and retention requirements can be different: somebody does not necessarily need to continuously meet the exact bar they joined under.

Jack also calculates guild-wide averages for supported statistics, giving the community a baseline for questions like:

- What does the average guild member's performance look like?
- Is a player above or below the guild average?
- Which areas is the roster strongest in?
- How do members compare with one another rather than with an arbitrary global number?

Together, the leaderboards, averages, activity reports, and requirement reports turn raw Hypixel data into a small analytics layer for the guild. Rankings and averages show the timestamp of the latest saved snapshot; Jack does not store a historical time series.

That gives staff better information for roster decisions while giving players a way to compare their current performance with the community.

Jack does **not** automatically remove players based on these reports. It surfaces the data and leaves membership decisions to staff.

### Moderation and community tools

Jack was built when Discord bots handled much more of a server's moderation logic themselves. Features like temporary mutes were commonly implemented by assigning a restricted role, storing the mute state, and having the bot remove that role after a custom duration. That gave communities more control over mute lengths and also made it possible for a bot to maintain its own moderation history or statistics.

Discord now provides native timeouts for much of this functionality, so Jack uses those where appropriate rather than recreating functionality the platform already handles. Staff can issue timed mutes, indefinite role-based mutes, kicks, bans, and unbans directly through the bot. Timed mutes expire through Discord itself, while role-based mutes remain available when a server needs behavior outside the native timeout system.

Moderation commands also check Discord permissions and role hierarchy so staff cannot act beyond their authority and Jack cannot moderate members above its own role.

Jack does not currently perform automatic slur or keyword filtering. That would be a separate moderation system if added later.

Alongside moderation, Jack includes community features such as staff-reviewed quote submissions, optional deleted-message retrieval, animal-image commands, latency checks, and a few intentionally unserious commands such as Mango.

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
