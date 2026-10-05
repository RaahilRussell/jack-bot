# Restoration notes

## Original behavior and baseline

The original bot had six command groups in flat Python modules. It used a Discord prefix, Mojang and Hypixel lookups, MongoDB snapshots, Pillow image cards, and a Flask keep-alive thread. It had no README or tests. All Python files parsed, but the declared discord.py 1.7.3 runtime rejected `message_content`; the source also expected newer asynchronous extension loading. `requests` and Pillow were imported without being declared directly.

The restoration keeps the same command families and Minecraft map cards. Existing command aliases are retained case-insensitively, including `pingg`, `ch`, `chgq`, `gq`, `ia`, `kicklist`, `a`, `average`, `r`, `reqs`, `invite`, `log`, `dc`, `channeldelete`, and `tempmute`.

## Intentional changes

- Default prefix: `j!`; customize `COMMAND_PREFIX` for an existing server.
- Configuration: `DISCORD_TOKEN`, `HYPIXEL_API_KEY`, and `HYPIXEL_GUILD` replace old environment names and embedded server details. Copy `.env.example`; no private server IDs or account-specific role privileges are embedded.
- Storage: a local SQLite snapshot replaces repeated synchronous MongoDB queries. This avoids a separate database service and missing seed records. Guild stats rebuild from Hypixel; old MongoDB mute records are not imported. Restore any roles removed by the old bot manually before retiring it.
- Leaderboards: one renderer replaces fifteen near-identical image generators. Images are generated in memory when requested instead of overwritten on disk every five minutes. Empty/small guilds are supported. Index now consistently uses stars × FKDR², names stay paired with values, Skywars averages use levels instead of XP, and all averages use arithmetic division.
- Moderation: timed mutes use native timeouts, capped at Discord's 28 days. Indefinite mutes only add the configured role; no roles are removed. Native permission checks replace account-specific staff roles. Closed DMs do not block kicks or bans. Unban supports user IDs and legacy exact tags. `spam` has a five-message maximum and suppresses mentions instead of looping forever.
- Applications: per-channel persistent records replace shared global applicant state. Private permissions are applied at creation. The old `delete` special case now aliases deletion of the current recorded application. No blacklist of server channel names is needed. The old unfiltered wait-for-any-message in `deny` is gone.
- Verification: handles current usernames, missing social links, and configured guild/rank roles. Old identity-specific privilege grants and targeted role-removal listeners are removed.
- Eligibility: the application and member-retention formulas remain distinct, as in the functioning checks of the original code. The contradictory requirements embed is corrected to describe both rather than silently changing eligibility.
- Community: quote moderation uses server permissions rather than fixed user/channel IDs. Deleted-message retrieval is channel-scoped and opt-in. The old listener that deleted every message in a channel named `applications` was removed; channel permissions can enforce a read-only channel without deleting command inputs.
- Assets: generated/test leaderboard screenshots with historical usernames, the old branded banner, unused background variants, an unused welcome font, and personal videos are omitted. Clean map images and the active font remain. Mango supports replacement videos from an ignored local directory. Penguin retains one external image; expired private attachment links are removed.
- Runtime: extensions load once in `setup_hook`; background jobs cancel and the shared HTTP session closes on shutdown. No credentials are read on module import. The empty help module, compiled bytecode, editor breakpoints, unused schedulers, Flask keep-alive, and dead Skyblock-weight request are gone.

## Deployment checks still requiring a real server

Offline checks do not prove credentials, guild permissions, external service availability, or live role assignment. In a test server, check `ping`, profile lookup, image delivery, verification with an explicitly linked account, application acceptance/denial, quote approval, and timed mute/unmute. Check the bot's role position and mapped rank roles before enabling verification.

A missing/expired API key produces a command error. Failed guild scans retain the prior complete snapshot; the timestamp identifies stale data. External image providers can change or disappear. There is no in-game bot, automatic kick system, or automatic invitation sender.

## Next improvements

After a live smoke test, consider explicit OAuth-style account linking, a more complete rate-limit retry/cache policy, and optional slash-command equivalents. Confirm project and map-asset licensing before making a public release. Keep changes small enough to preserve the original project.
