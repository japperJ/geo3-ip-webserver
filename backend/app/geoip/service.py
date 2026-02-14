from __future__ import annotations

from typing import Any

from app.geoip.cache import GeoIPCache


class GeoIPService:
    def __init__(
        self,
        *,
        cache: GeoIPCache,
        reader: object | None,
        db_session: object | None = None,
    ) -> None:
        self._cache = cache
        self._reader = reader
        self._db_session = db_session

    def lookup(self, ip: str) -> dict[str, object] | None:
        cached = self._cache.get(ip)
        if cached is not None:
            return cached

        db_cached = self._fetch_from_db(ip)
        if db_cached is not None:
            self._cache.set(ip, db_cached)
            return db_cached

        if self._reader is None:
            raise RuntimeError("MaxMind reader not available")

        lookup = getattr(self._reader, "city", None)
        if lookup is None:
            raise RuntimeError("MaxMind reader not available")

        data = self._normalize(lookup(ip))
        self._cache.set(ip, data)
        self._store_in_db(ip, data)
        return data

    def _fetch_from_db(self, ip: str) -> dict[str, object] | None:
        if self._db_session is None:
            return None
        query = getattr(self._db_session, "query", None)
        if query is None:
            return None
        result = query(ip)
        if result is None:
            return None
        if isinstance(result, dict):
            return result
        raw = getattr(result, "raw", None)
        if isinstance(raw, dict):
            return raw
        return None

    def _store_in_db(self, ip: str, data: dict[str, object]) -> None:
        if self._db_session is None:
            return
        add = getattr(self._db_session, "add", None)
        commit = getattr(self._db_session, "commit", None)
        if add is None or commit is None:
            return
        try:
            from app.db.models.ip_geo_cache import IpGeoCache
        except Exception:
            return
        try:
            record = IpGeoCache(ip_address=ip, raw=data)
            add(record)
            commit()
        except Exception:
            return

    def _normalize(self, response: Any) -> dict[str, object]:
        if isinstance(response, dict):
            return response
        country = getattr(getattr(response, "country", None), "iso_code", None)
        location = getattr(response, "location", None)
        if location is not None:
            lat = getattr(location, "latitude", None)
            lon = getattr(location, "longitude", None)
        else:
            lat = None
            lon = None
        payload: dict[str, object] = {}
        if country is not None:
            payload["country_code"] = country
        if lat is not None and lon is not None:
            payload["latitude"] = lat
            payload["longitude"] = lon
        return payload
