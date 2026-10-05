"""Configuration is read at startup, never as an import side effect."""

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    token: str = field(default="", repr=False)
    hypixel_key: str = field(default="", repr=False)
    prefix: str = "j!"
    guild_name: str = ""
    data_dir: Path = Path("data")
    media_dir: Path = Path("media")
    staff_role: str = "Staff"
    accepted_role: str = "Accepted"
    member_role: str = "Member"
    guest_role: str = "Guest"
    unverified_role: str = "Unverified"
    muted_role: str = "Muted"
    waiting_channel: str = "invite-waiting-list"
    invite_channel: str = "invite-log"
    quote_channel: str = "quote-book"
    quote_submissions: str = "quote-book-submissions"
    snipe_enabled: bool = False
    guild_rank_roles: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if env is None else env
        prefix = values.get("COMMAND_PREFIX", "j!").strip()
        if not prefix or len(prefix) > 10:
            raise ValueError("COMMAND_PREFIX must contain 1–10 characters.")
        try:
            rank_roles = json.loads(values.get("GUILD_RANK_ROLES", "{}"))
        except ValueError:
            raise ValueError(
                "GUILD_RANK_ROLES must be a JSON object mapping guild ranks to role names."
            ) from None
        if not isinstance(rank_roles, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and v for k, v in rank_roles.items()
        ):
            raise ValueError(
                "GUILD_RANK_ROLES must map guild rank names to nonempty Discord role names."
            )
        return cls(
            token=values.get("DISCORD_TOKEN", "").strip(),
            hypixel_key=values.get("HYPIXEL_API_KEY", "").strip(),
            prefix=prefix,
            guild_name=values.get("HYPIXEL_GUILD", "").strip(),
            data_dir=Path(values.get("DATA_DIR", "data")),
            media_dir=Path(values.get("MEDIA_DIR", "media")),
            **{
                name: values.get(name.upper(), default)
                for name, default in {
                    "staff_role": "Staff",
                    "accepted_role": "Accepted",
                    "member_role": "Member",
                    "guest_role": "Guest",
                    "unverified_role": "Unverified",
                    "muted_role": "Muted",
                    "waiting_channel": "invite-waiting-list",
                    "invite_channel": "invite-log",
                    "quote_channel": "quote-book",
                    "quote_submissions": "quote-book-submissions",
                }.items()
            },
            snipe_enabled=values.get("ENABLE_SNIPE", "false").lower() == "true",
            guild_rank_roles=rank_roles,
        )
