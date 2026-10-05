# Screenshot capture guide

[Back to Jack](../../README.md)

No anonymized live screenshots are currently bundled. Add captures of actual bot output after completing the [test-server checklist](../setup.md#live-smoke-test-checklist); do not manufacture Discord conversations or label generated mockups as a live demo.

## Suggested captures

| File | Capture | What it demonstrates |
| --- | --- | --- |
| `leaderboard.png` | A top-ten card delivered by `lb` | Stat aggregation, sorting, Pillow rendering, Minecraft styling |
| `application.png` | A private application and staff decision | Permission-aware channel creation and persistent applicant tracking |
| `verification.png` | A successful verification and an unmatched-account rejection | REST integration, validation, and role workflow |
| `help.png` | A readable crop of `j!help` | The command groups and the bot's original personality |

These are suggested filenames, not existing images. One strong leaderboard capture and one application/verification capture are enough for the README.

## Anonymize before committing

- Use a disposable test server and accounts you control. Replace visible identity labels with neutral labels such as “Player A”, “Applicant”, and “Reviewer”; state in the caption that labels were anonymized.
- Remove real usernames, avatars, Discord IDs, server/channel names, member lists, invites, account menus, private messages, and notifications from the capture. Check the leaderboard's embedded player names as well as Discord's surrounding UI.
- Never show developer-portal token fields, `.env`, API keys, log output, or local filesystem paths. Do not upload raw screenshots to this repository as an intermediate step.
- Use opaque redaction or cropping; do not rely on a light blur. Flatten the result, strip image metadata, reopen it, and inspect it at full size.
- Keep the output and workflow truthful. If labels are anonymized or data comes from a test guild, say so; do not imply production usage, adoption, or performance measurements.

After reviewing the images, replace the README's screenshot placeholder with relative image links, concise captions, and useful alt text. Keep the map/font attribution in `CREDITS.md` intact.
