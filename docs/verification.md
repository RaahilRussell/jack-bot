# Verification record

## Local checks

- Original Python files parsed, but the pinned Discord 1.7.3 runtime failed on `Intents.message_content`; it could not run the entry point as declared.
- 95 offline tests passed in the final polish pass. Tests cover stat boundaries, API failures, credential-header redirects, sparse profiles, sorting, image rendering, fractional averages, storage persistence, application isolation, moderation hierarchy, and extension startup/shutdown. GitHub Actions runs the suite on Python 3.11–3.14.
- `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy` passed.
- `uv run python -m jack --check` loaded six command groups and 29 primary commands, plus aliases, without network calls.
- `uv build` produced a wheel and source distribution. An isolated install of the wheel loaded all extensions and rendered a card using the packaged assets.
- The locked runtime dependency set passed `pip-audit`; no known vulnerabilities were reported. This is a point-in-time audit, not a guarantee against undiscovered vulnerabilities.
- Animal endpoint smoke checks for cat, red panda, bird, duck, and the retained penguin image returned HTTP 200. This does not guarantee future availability.
- The representative rendered card was inspected visually. Retained map images have no embedded text metadata; the font retains its original copyright and license metadata.

## Final presentation pass

The README now leads with the bot's purpose, engineering highlights, grouped features, and architecture. Detailed configuration and command usage moved into [setup](setup.md) and [commands](commands.md). The reference was compared with the loaded command registry: all 29 primary commands and 23 aliases are covered, including `help`. All 18 example environment variables are documented, and relative documentation links resolve.

`uv sync --locked`, Ruff lint and format checks, mypy, pytest, offline startup, and `uv build` passed locally. A full `uv run pip-audit` reported no known dependency vulnerabilities; the local Jack package was skipped because it is not published on PyPI. No lint/type settings or existing tests were weakened.

Compatibility was checked against installed discord.py 2.7.1 and its [2.x migration guide](https://discordpy.readthedocs.io/en/stable/migrating.html). The implementation supplies the required intents, awaits extension/cog loading, uses `setup_hook`, closes its shared HTTP session, cancels the leaderboard task on unload, uses `Member.timeout`, passes `delete_message_seconds` for bans, and iterates `Guild.bans` asynchronously. Permission decorators and member/message intent requirements match the documented setup. Live platform behavior still requires the checks below.

The architecture and workflows were preserved. The only runtime change in this pass prevents requests carrying custom credential headers from following redirects: a local two-server regression reproduced header forwarding before the fix and confirmed that authenticated redirects are now blocked while public redirects still work. The animal command's help text was also corrected because the penguin image is fixed rather than random.

## Privacy cleanup

A redacted Gitleaks scan covered the original Git history and the cleaned release tree. Additional credential-pattern checks covered all 236 historical file blobs, including compiled Python files. No committed credentials were found by these checks.

Sensitive configuration found in the old source was removed rather than copied into the new defaults:

- `somecommands.py`: fixed user IDs, a submission-channel ID, account-specific command responses and role checks.
- `hypixelcommands.py`: fixed channel/user IDs, an old Discord tag, account-specific privilege changes, and guild identity strings.
- `moderativecommands.py`: account-specific permissions and obsolete personal asset URLs.
- `main.py`, `leaderboards.py`, and package metadata: old branding and guild-specific defaults.
- Old generated/test leaderboard screenshots and the banner: visible historical player names and branding. Bytecode, editor metadata, unused assets, and old video clips were removed from the new tree.
- `hypixel.py` and `hypixelcommands.py`: logging of request URLs containing the runtime API key. These prints were removed; keys now travel in request headers. If an old deployment retained these logs, rotate its Hypixel key and remove the sensitive logs there.

The final release-tree scan found no old project/author identity strings, personal account URLs, or embedded Discord snowflake IDs. Historical third-party contributor and font attribution remain in `CREDITS.md`.

The presentation pass rechecked authored files, asset metadata, URLs, and ignore rules. No new identifying content, committed credentials, historical screenshots, private media, local filesystem paths, or editor metadata were found. The generic role/channel defaults and public API/image-provider URLs remain intentional. `.gitignore` also now covers alternate SQLite/database extensions and the `logs/` directory; `.env.example` remains includable. Credits and the four original map/font assets were not changed. No screenshots were invented; [the capture guide](screenshots/README.md) describes what to add after a live run.

## Limits

No Discord login, moderation action, live application, or authenticated Hypixel request was performed. Those require operator-supplied credentials and a test server. The Discord dependency emits upstream deprecation warnings on some Python versions; they do not fail these checks. This bot has no voice features and intentionally omits optional voice dependencies.

The old MongoDB state is not imported. Guild leaderboards rebuild, but any roles previously stripped by the old bot need manual restoration. Bundled map-art licensing still needs confirmation before a public release.
