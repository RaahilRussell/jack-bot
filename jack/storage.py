"""Small local snapshots; each operation uses its own connection off the event loop."""

import asyncio
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


class Store:
    def __init__(self, path: Path):
        self.path = path

    def _query(self, sql: str, params: tuple = ()) -> list[tuple]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=10)) as connection:
            with connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
                )
                return connection.execute(sql, params).fetchall()

    async def get(self, key: str) -> Any:
        rows = await asyncio.to_thread(self._query, "SELECT value FROM state WHERE key = ?", (key,))
        return json.loads(rows[0][0]) if rows else None

    async def put(self, key: str, value: Any) -> None:
        await asyncio.to_thread(
            self._query,
            "INSERT INTO state VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._query, "DELETE FROM state WHERE key = ?", (key,))
