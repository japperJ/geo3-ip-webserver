from __future__ import annotations

import time


class GeoIPCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, dict[str, object]]] = {}

    def get(self, ip: str) -> dict[str, object] | None:
        entry = self._items.get(ip)
        if entry is None:
            return None
        expires_at, payload = entry
        if time.time() >= expires_at:
            self._items.pop(ip, None)
            return None
        return payload

    def set(self, ip: str, data: dict[str, object]) -> None:
        expires_at = time.time() + self._ttl_seconds
        self._items[ip] = (expires_at, data)
