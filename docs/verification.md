# Verification record

## Local checks

- Original Python files parsed, but the pinned Discord 1.7.3 runtime failed on `Intents.message_content`; it could not run the entry point as declared.
- 93 offline tests passed on Python 3.11, 3.12, and 3.14. Tests cover stat boundaries, API failures, sparse profiles, sorting, image rendering, fractional averages, storage persistence, application isolation, moderation hierarchy, and extension startup/shutdown.
- `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy` passed.
- `uv run python -m jack --check` loaded six command groups and 29 primary commands, plus aliases, without network calls.
- `uv build` produced a wheel and source distribution. An isolated install of the wheel loaded all extensions and rendered a card using the packaged assets.
- The locked runtime dependency set passed `pip-audit`; no known vulnerabilities were reported. This is a point-in-time audit, not a guarantee against undiscovered vulnerabilities.
- Animal endpoint smoke checks for cat, red panda, bird, duck, and the retained penguin image returned HTTP 200. This does not guarantee future availability.
- The representative rendered card was inspected visually. Retained map images have no embedded text metadata; the font retains its original copyright and license metadata.

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

## Limits

No Discord login, moderation action, live application, or authenticated Hypixel request was performed. Those require operator-supplied credentials and a test server. The Discord dependency emits upstream deprecation warnings on some Python versions; they do not fail these checks. This bot has no voice features and intentionally omits optional voice dependencies.

The old MongoDB state is not imported. Guild leaderboards rebuild, but any roles previously stripped by the old bot need manual restoration. Bundled map-art licensing still needs confirmation before a public release.
