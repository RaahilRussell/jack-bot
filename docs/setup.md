# Setup and server configuration

[Back to Jack](../README.md) · [Command reference](commands.md)

## Install and check

Use Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/). From the repository directory:

```sh
uv sync --locked
cp .env.example .env
uv run python -m jack --check
```

The check loads the command groups without a Discord login or external requests. Edit `.env` locally; never paste tokens into source code, screenshots, issues, or commits. Existing environment variables take precedence over `.env` values.

## Discord application and intents

Create an application and bot in the [Discord developer portal](https://discord.com/developers/applications). Put its **bot token** in `DISCORD_TOKEN`; a personal account token is not supported.

Enable these privileged gateway intents on the application's Bot page:

- **Message Content Intent:** required to read prefix commands and quote text.
- **Server Members Intent:** required for member caching, role workflows, and the join listener.

The code enables both intents along with the default guild, message, and reaction intents. Presence Intent is not required. See the [discord.py intent guide](https://discordpy.readthedocs.io/en/stable/intents.html) if the connection is rejected or commands receive no message text.

Use the portal's installation/OAuth settings to invite the bot to a test server with the `bot` scope. Jack uses prefix commands, so it does not need slash-command registration.

## Permissions and hierarchy

In channels where Jack operates, grant **View Channels**, **Send Messages**, **Embed Links**, **Attach Files**, **Read Message History**, and **Add Reactions**. Channel overrides must allow these as well as the server role. Additional permissions depend on enabled features:

| Feature | Bot permissions | Server setup |
| --- | --- | --- |
| Verification and join roles | Manage Roles; Manage Nicknames for `verify` | Member, Guest, optional Unverified roles |
| Applications | Manage Channels, Manage Roles | Staff and Accepted roles; waiting-list channel |
| Invitation log | Send Messages in the log channel | Invitation-log channel |
| Quote review | Manage Messages | Submission and destination channels |
| Timed mute / unmute | Moderate Members | Target below Jack's role |
| Indefinite mute / role removal | Moderate Members, Manage Roles | Muted role with appropriate channel overrides |
| Kick / ban / unban | Kick Members or Ban Members, respectively | Targets below Jack's role for kick/ban |

Administrator is not required. Place Jack's highest role above roles it assigns/removes and members it moderates. Assignable roles must not be integration-managed or `@everyone`. The configured Staff role only needs to exist for application channel access; it need not sit below Jack.

Users need the corresponding Discord moderation permission to mute, kick, ban, or unban. Staff workflow commands accept the configured Staff role **or** Manage Server. Quote approval accepts that role **or** Manage Messages. `status` and `spam` require the bot application owner as determined by discord.py, not merely the server owner. See [commands](commands.md) for per-command details.

A timed mute uses Discord's native timeout and lasts at most 28 days. An indefinite mute only adds the configured Muted role; set channel overrides denying sending messages and speaking. Other role overrides can defeat those denials, so test this with a non-privileged account. Jack never strips existing roles. Discord rejects timeouts for administrators and the server owner.

Application channels are created with private overwrites for the applicant, Staff, and Jack. Server administrators still have access. Manage Server alone permits staff commands but does not bypass Discord channel visibility; grant the Staff role to reviewers who need access.

## Hypixel and Minecraft

Create a key through the [Hypixel developer dashboard](https://developer.hypixel.net/) and set `HYPIXEL_API_KEY`. Set `HYPIXEL_GUILD` to the guild to report on and verify membership against. Mojang username lookup needs no key. Basic community and moderation commands work without either Hypixel setting.

Jack uses the [Hypixel v2 API](https://api.hypixel.net/), sends the key in a header, and spaces its Hypixel requests at least two seconds apart. The key's quota can also be consumed by other applications; rate-limit errors are reported without automatic retries. Requests time out after 20 seconds. Calls carrying credential headers do not follow redirects.

With both Hypixel settings present, a complete guild-stat snapshot refreshes every two hours. The initial scan can take several minutes; subsequent failures retain the previous snapshot and its timestamp. Leaderboards and `gamereqs` use these snapshots. Individual profile checks and `inactive` query the services directly.

For `verify`, the user must link their current Discord **username** in Hypixel's social settings. Jack compares that value to the invoking account, updates configured membership/rank roles, and attempts a Minecraft-name nickname. This is username matching, not OAuth account linking. `apply` accepts a supplied Minecraft name for recruitment review and does not itself prove account ownership.

## Environment variables

All defaults below are generic configuration labels, not references to a private server. Relative paths resolve from the process's working directory.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DISCORD_TOKEN` | Empty | Required for a live Discord login; secret |
| `HYPIXEL_API_KEY` | Empty | Required for Hypixel requests; secret |
| `HYPIXEL_GUILD` | Empty | Guild name for verification, reports, and snapshots |
| `COMMAND_PREFIX` | `j!` | Prefix of 1–10 characters |
| `DATA_DIR` | `data` | Persistent state directory |
| `MEDIA_DIR` | `media` | Optional local Mango videos |
| `ENABLE_SNIPE` | `false` | Set to `true` to enable deleted-text retrieval |
| `GUILD_RANK_ROLES` | `{}` | JSON mapping of Hypixel ranks to Discord role names |

### Role names

| Variable | Default | Purpose |
| --- | --- | --- |
| `STAFF_ROLE` | `Staff` | Application review and quote moderation |
| `ACCEPTED_ROLE` | `Accepted` | Accepted applicants awaiting invitations |
| `MEMBER_ROLE` | `Member` | Verified members of the configured Hypixel guild |
| `GUEST_ROLE` | `Guest` | Verified users outside the configured guild |
| `UNVERIFIED_ROLE` | `Unverified` | Added on joining, if the role exists and is editable |
| `MUTED_ROLE` | `Muted` | Indefinite role-based mutes |

### Channel names

| Variable | Default | Purpose |
| --- | --- | --- |
| `WAITING_CHANNEL` | `invite-waiting-list` | Accepted applicant notifications |
| `INVITE_CHANNEL` | `invite-log` | Manual invitation records |
| `QUOTE_CHANNEL` | `quote-book` | Approved quotes |
| `QUOTE_SUBMISSIONS` | `quote-book-submissions` | Messages receive approve/reject reactions |

Use exact role/channel names, without a leading `#`. Create resources for the features you use; Jack reports missing roles/channels rather than silently creating a server layout. Application channels themselves are created by `apply`.

### Guild rank mapping

An optional mapping can assign additional Discord roles to in-game ranks:

```dotenv
GUILD_RANK_ROLES={"Veteran":"Veteran"}
```

Only map roles you intend this verification workflow to control. Jack may add or remove any mapped role as membership changes; unrelated roles remain untouched. No staff ranks are mapped by default. Keep Member, Guest, and Unverified distinct, and avoid mapping a guild rank to Guest or Unverified.

## State, media, and optional features

SQLite lives at `DATA_DIR/jack.sqlite3`. The directory is created on first use and must be writable. Keep it on persistent storage and run **one Jack process per data directory**. It contains runtime applicant identifiers and guild snapshots, so keep backups private. Restarting preserves application records; deleting the database loses those records and prevents Jack from managing existing application channels. Leaderboards can be rebuilt from Hypixel. Old MongoDB mute records are not imported; see [migration notes](modernization.md).

Mango replies with “Mango...” and optionally sends a random `.mp4` or `.mov` from `MEDIA_DIR` that fits the channel's upload limit. No personal clips are bundled. Use media you have permission to share. Both default data and media directories are ignored by Git; if you choose different directories inside the checkout, add them to `.gitignore` too.

`ENABLE_SNIPE=true` lets users retrieve the most recent deleted text message in its original channel for five minutes. It only sees messages cached by the running bot, keeps at most 100 channel entries in memory, and clears on restart. Expired entries cannot be retrieved, but may remain in memory until accessed or evicted. It does not save text to SQLite or logs. Leave it disabled if deleted messages should not be recoverable.

## Run

```sh
uv run python -m jack
```

`uv run jack-bot` and `uv run python main.py` are equivalent. Keep the process running on your host with the same working directory or explicit data/media paths. There is no embedded web server, voice subsystem, or artificial keep-alive service.

## Live smoke-test checklist

Use a disposable test server and accounts you control. These checks have **not** been replaced by offline tests:

- [ ] Connect with both intents enabled; run `j!ping` and `j!help`.
- [ ] Try a valid and invalid Minecraft lookup; check a missing/expired Hypixel key gives a useful error.
- [ ] Render a leaderboard and inspect its timestamp; restart and confirm the saved snapshot remains usable.
- [ ] Verify an explicitly linked account; reject an unmatched one; inspect membership/rank roles and nickname permissions.
- [ ] Open an application below the automatic threshold; confirm an unrelated member cannot see its channel.
- [ ] Restart with two applications open; accept/deny each and confirm the correct user is affected. Confirm `deletechannel` rejects an ordinary channel.
- [ ] Check automatic acceptance and the waiting-list message with an eligible account. Log an invite; confirm it does not claim to send an in-game invite.
- [ ] Approve/reject a quote as staff; confirm an ordinary user's reaction cannot approve it.
- [ ] Try moderation as an unauthorized user, against a higher role, and against a disposable eligible account. Confirm timed mute expiry and role preservation, then kick/ban/unban behavior.
- [ ] Test optional videos and, if enabled, snipe isolation/expiry. Confirm no private data appears in logs or planned screenshots.
