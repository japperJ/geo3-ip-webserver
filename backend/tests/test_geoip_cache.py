from app.geoip.cache import GeoIPCache
from app.geoip.service import GeoIPService


def test_geoip_cache_hit():
    cache = GeoIPCache(ttl_seconds=60)
    cache.set("1.2.3.4", {"country_code": "US"})

    assert cache.get("1.2.3.4") == {"country_code": "US"}


def test_geoip_service_cache_hit_skips_reader():
    cache = GeoIPCache(ttl_seconds=60)
    cache.set("1.2.3.4", {"country_code": "US"})
    service = GeoIPService(cache=cache, reader=None)

    assert service.lookup("1.2.3.4") == {"country_code": "US"}
