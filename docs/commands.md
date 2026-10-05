# Command reference

[Back to Jack](../README.md) · [Server setup](setup.md)

The tables cover all **29 registered primary commands** and their aliases. Prefix every command with `j!` (or `COMMAND_PREFIX`). Names and aliases are case-insensitive. `<argument>` is required, `[argument]` is optional; do not type the brackets. `ign` means Minecraft username, and `member` accepts a Discord member mention or another unambiguous member identifier supported by discord.py.

**Permission** describes the invoking user. “Anyone” still requires access to the channel; “server” means the command cannot run in DMs. “Staff” means the configured Staff role or Manage Server. “Bot owner” means the Discord application owner recognized by discord.py. Jack's own permissions are listed in [setup](setup.md#permissions-and-hierarchy).

## Community and utilities

| Command | Arguments | Aliases | Permission | Description |
| --- | --- | --- | --- | --- |
| `help` | `[command]` | — | Anyone | Show command groups or usage for one command. |
| `ping` | — | `pingg` | Anyone | Show gateway and message latency. |
| `mango` | — | — | Anyone | Reply “Mango...” and optionally send a local video within the upload limit. |
| `status` | `<text...>` | — | Bot owner | Set the bot's presence text, up to 128 characters. |
| `snipe` | — | — | Anyone, server | Retrieve the latest deleted text in this channel within five minutes; requires `ENABLE_SNIPE=true`. |
| `cat` | — | `rpanda`, `panda`, `bird`, `koala`, `duck`, `penguin` | Anyone | Send an animal image. Each alias selects that species; `rpanda` is red panda. Penguin uses a fixed external photo; the others use random-image APIs. |
| `fart` | — | — | Anyone | Send the original playful response naming the invoking user. |

Quote moderation is an event workflow, not another command: messages in the configured submission channel receive ✅ and ❌ reactions. Staff-role members or users with Manage Messages can approve a quote for the destination channel or reject it; the submission is then deleted. Other reactions do not approve it.

## Hypixel, guilds, and applications

| Command | Arguments | Aliases | Permission | Description |
| --- | --- | --- | --- | --- |
| `discord` | `<ign>` | — | Anyone | Read the Discord username publicly linked on a Hypixel profile. |
| `void` | `<ign>` | — | Anyone | Show Bedwars void deaths. |
| `check` | `<ign>` | `ch`, `chgq` | Anyone | Check application eligibility against the original game-stat rule. |
| `requirements` | — | `r`, `reqs` | Anyone | Explain application and existing-member thresholds. |
| `apply` | `<username>` | — | Anyone, server | Add an eligible applicant to the waiting list, or open a private staff-review channel. |
| `accept` | `[ign]` | — | Staff, server | Accept the recorded applicant in this channel; optionally override the Minecraft name. Close the channel after ten seconds. |
| `deny` | — | — | Staff, server | Deny the recorded application and close its channel after ten seconds. |
| `deletechannel` | — | `dc`, `channeldelete`, `delete` | Staff, server | Immediately close the current recorded application channel; refuses ordinary channels. |
| `accepted` | `<member>` | — | Staff, server | Toggle the configured Accepted role. |
| `verify` | `<ign>` | — | Anyone, server | Match the Hypixel-linked Discord username, update configured membership/rank roles, and attempt a nickname update. |
| `inactive` | — | `kicklist`, `ia` | Staff, server | List guild members below 100,000 weekly guild XP; never kick automatically. |
| `gamereqs` | — | `gamerequirements`, `gq` | Anyone | Report members below retention requirements from the cached guild snapshot. |
| `invited` | `<ign>` | `log`, `invite` | Staff, server | Record a manual invitation and eligibility result; does not send an in-game invite. |

Application and retention requirements intentionally differ. Applications require index ≥ 2,000, or index ≥ 1,000 plus 3,000 Duels wins and 2 WLR. Retention requires 150 Bedwars stars and 1 FKDR, plus either index ≥ 1,000 or index ≥ 650 with 1,000 Duels wins and 1 WLR. Index is stars × FKDR²; a zero-denominator ratio keeps the original value of zero.

## Leaderboards

| Command | Arguments | Aliases | Permission | Description |
| --- | --- | --- | --- | --- |
| `lb` | `[game] [stat] [scope]` | — | Anyone | Show usage with no game; otherwise render a top-ten card. `scope=all` or `a` returns the full text ranking. |
| `avg` | `[game=bw] [stat]` | `a`, `average` | Anyone | Show a guild stat's arithmetic mean, or a no-data message for an empty guild. |

| Game | Game aliases | Supported stats | Default stat |
| --- | --- | --- | --- |
| `bw` | `b`, `bedwars` | `star`, `fkdr`, `index`, `wins`, `finals`, `wlr` | `star` |
| `sw` | `s`, `skywars` | `star`, `kills`, `wins`, `kdr` | `star` |
| `duels` | `d`, `duel` | `wins`, `kills`, `wlr`, `kdr`, `bridge_wins` | `wins` |

Stat shortcuts: `s`/`stars` → `star`; `fk`/`fkd` → `fkdr`; `i` → `index`; `f`/`final` → `finals`; `w`/`win` → `wins`; `wl`/`wlrs` → `wlr`; `k`/`kill` → `kills`; `kd` → `kdr`; `bw`/`bridge_win` → `bridge_wins`. Only stats valid for the selected game are accepted.

```text
j!lb bw star
j!lb duels bridge_wins all
j!avg sw kdr
```

These commands show the snapshot timestamp. The first scan may take several minutes; a failed refresh preserves the previous complete snapshot.

## Moderation

| Command | Arguments | Aliases | Permission | Description |
| --- | --- | --- | --- | --- |
| `mute` | `<member> [duration] [reason...]` | `tempmute` | Moderate Members, server | Apply a native timeout; omit duration to add the configured Muted role indefinitely. |
| `unmute` | `<member>` | — | Moderate Members, server | Clear the timeout and configured Muted role, preserving unrelated roles. |
| `kick` | `<member> [reason...]` | — | Kick Members, server | Attempt a reason DM, then kick; closed DMs do not block the action. |
| `ban` | `<member> [reason...]` | — | Ban Members, server | Attempt a reason DM, then ban without deleting message history. |
| `unban` | `<user-id or exact username>` | — | Ban Members, server | Unban by user ID or an exact username from the ban list, including legacy tags. |
| `member` | `<member>` | — | Anyone, server | List a member's role names. |
| `spam` | `<member> [count=3]` | — | Bot owner, server | Send 1–5 playful mentions at one-second intervals without mention notifications. |

Durations use a positive integer followed by `s`, `m`, `h`, or `d`, such as `10m`; timeouts cannot exceed 28 days. To supply a mute reason, include a duration first. Omitting a duration means invoking `mute <member>` with no reason. Kick/ban/mute reasons can contain spaces and otherwise default to “No reason supplied”. Moderation checks both user and bot role hierarchy; the server owner, the bot itself, and the invoking user cannot be targeted.

## Cooldowns and concurrency

- Per user: animal commands share 1 use / 2 seconds; Mango and `lb`/`avg` each allow 1 / 5 seconds; `check` allows 1 / 10 seconds.
- Per member within a server: `apply` allows 1 / 60 seconds; `verify` allows 1 / 15 seconds.
- Per server: `inactive` and `spam` each allow 1 / 60 seconds; `gamereqs` allows 1 / hour. For `gamereqs` in DMs, discord.py uses the invoking user's bucket.
- `apply` allows one active invocation per server; `accept` allows one per channel. Existing recorded applications prevent duplicate open channels for the same applicant.

Aliases share their primary command's cooldown. A visible command does not imply the caller has permission to run it; use `j!help <command>` for in-Discord usage.
