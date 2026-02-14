import importlib

import pytest
from pydantic import ValidationError

from app.geoip.cache import GeoIPCache
from app.geoip.service import GeoIPService


def test_geoip_cache_hit():
    cache = GeoIPCache(ttl_seconds=60)
    cache.set("1.2.3.4", {"country_code": "US"})

    assert cache.get("1.2.3.4") == {"country_code": "US"}


def test_geoip_cache_expired_entry_returns_none(monkeypatch):
    import app.geoip.cache as cache_module

    now = 1000.0
    monkeypatch.setattr(cache_module.time, "time", lambda: now)
    cache = GeoIPCache(ttl_seconds=60)
    cache.set("1.2.3.4", {"country_code": "US"})

    now = 1060.0
    assert cache.get("1.2.3.4") is None


def test_geoip_cache_rejects_non_positive_ttl():
    with pytest.raises(ValueError):
        GeoIPCache(ttl_seconds=0)
    with pytest.raises(ValueError):
        GeoIPCache(ttl_seconds=-1)


def test_geoip_service_cache_hit_skips_reader():
    cache = GeoIPCache(ttl_seconds=60)
    cache.set("1.2.3.4", {"country_code": "US"})
    service = GeoIPService(cache=cache, reader=None)

    assert service.lookup("1.2.3.4") == {"country_code": "US"}


def test_geoip_service_missing_reader_raises():
    cache = GeoIPCache(ttl_seconds=60)
    service = GeoIPService(cache=cache, reader=None)

    with pytest.raises(RuntimeError, match="reader"):
        service.lookup("1.2.3.4")


def test_settings_rejects_non_positive_geoip_ttl(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    settings_module = importlib.import_module("app.settings")
    importlib.reload(settings_module)

    with pytest.raises(ValidationError):
        settings_module.Settings(jwt_secret="x" * 32, geoip_cache_ttl_seconds=0)
    with pytest.raises(ValidationError):
        settings_module.Settings(jwt_secret="x" * 32, geoip_cache_ttl_seconds=-5)
