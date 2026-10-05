"""Shared, bounded HTTP access. Credentials only travel in Hypixel headers."""

import asyncio
import re
import time
from typing import Any

import aiohttp


class ServiceError(Exception):
    """An upstream failure with a message safe to show in Discord."""


class API:
    def __init__(self, session: aiohttp.ClientSession, key: str = ""):
        self.session = session
        self.key = key
        self._hypixel_lock = asyncio.Lock()
        self._next_request = 0.0

    async def json(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            async with self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
                # Redirect handling does not strip custom API-Key headers.
                allow_redirects=not bool(headers),
            ) as response:
                if response.status in (204, 404):
                    raise ServiceError("That player or resource could not be found.")
                if response.status == 429:
                    raise ServiceError("The service is rate limited. Please try again later.")
                if response.status in (401, 403):
                    raise ServiceError("The service rejected access. Check the configured API key.")
                if response.status != 200:
                    raise ServiceError(
                        "The service is temporarily unavailable. Please try again later."
                    )
                data = await response.json()
                if not isinstance(data, dict):
                    raise ServiceError("The service returned an unexpected response.")
                return data
        except (aiohttp.ClientError, TimeoutError, ValueError):
            # Raw HTTP exceptions can contain URLs; do not expose them to users/logs.
            raise ServiceError(
                "Could not read the service response. Please try again later."
            ) from None

    async def hypixel(self, endpoint: str, **params: str) -> dict[str, Any]:
        if not self.key:
            raise ServiceError("Hypixel commands need HYPIXEL_API_KEY in the bot configuration.")
        async with self._hypixel_lock:
            # Guild scans must leave room for interactive requests and other key users.
            await asyncio.sleep(max(0, self._next_request - time.monotonic()))
            self._next_request = time.monotonic() + 2.0
            data = await self.json(
                f"https://api.hypixel.net/v2/{endpoint}",
                params=params,
                headers={"API-Key": self.key},
            )
        if not data.get("success"):
            raise ServiceError("Hypixel could not complete that request.")
        return data

    async def profile(self, name: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", name):
            raise ServiceError("Enter a Minecraft username (1–16 letters, numbers or underscores).")
        data = await self.json(f"https://api.mojang.com/users/profiles/minecraft/{name}")
        if not data.get("id") or not data.get("name"):
            raise ServiceError("Minecraft returned an incomplete profile.")
        return data

    async def player(self, uuid: str) -> dict[str, Any]:
        data = await self.hypixel("player", uuid=uuid)
        if not isinstance(data.get("player"), dict):
            raise ServiceError("This player has no Hypixel profile yet.")
        return data["player"]

    async def guild(self, *, name: str = "", player: str = "") -> dict[str, Any] | None:
        if not name and not player:
            raise ServiceError("Set HYPIXEL_GUILD to your guild's name first.")
        data = await self.hypixel("guild", **({"player": player} if player else {"name": name}))
        guild = data.get("guild")
        if guild is not None and not isinstance(guild, dict):
            raise ServiceError("Hypixel returned an incomplete guild.")
        return guild
