import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-should-be-at-least-32-characters")

from app.db.models.site import SiteFilterMode
from app.main import app
from app.middleware.access_gate import SiteAccessConfig, clear_site_configs, register_site_config


def _setup_site_config(hostname: str, config: SiteAccessConfig) -> None:
    clear_site_configs(app)
    register_site_config(app, hostname, config)


def test_blocked_request_returns_403():
    _setup_site_config(
        "blocked.local",
        SiteAccessConfig(filter_mode=SiteFilterMode.IP, ip_rules=[]),
    )

    client = TestClient(app, client=("10.1.2.3", 50000))
    resp = client.get("/", headers={"Host": "blocked.local"})

    assert resp.status_code == 403


def test_allowed_request_allows_ip_match():
    _setup_site_config(
        "allowed.local",
        SiteAccessConfig(
            filter_mode=SiteFilterMode.IP,
            ip_rules=[{"cidr": "10.1.2.3/32", "action": "allow"}],
        ),
    )

    client = TestClient(app, client=("10.1.2.3", 50000))
    resp = client.get("/health", headers={"Host": "allowed.local"})

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_geo_allows_when_geoip_lookup_returns_truthy():
    class GeoService:
        def lookup(self, ip: str):
            return {"country_code": "US"}

    _setup_site_config(
        "geo.local",
        SiteAccessConfig(filter_mode=SiteFilterMode.GEO, ip_rules=[], geo_allowed=None),
    )

    client = TestClient(app, client=("203.0.113.10", 50000))
    client.app.state.geoip_service = GeoService()
    resp = client.get("/health", headers={"Host": "geo.local"})

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_ip_and_geo_requires_both_allow_and_geo():
    class GeoService:
        def lookup(self, ip: str):
            return True

    _setup_site_config(
        "ipgeo.local",
        SiteAccessConfig(
            filter_mode=SiteFilterMode.IP_AND_GEO,
            ip_rules=[{"cidr": "10.2.3.4/32", "action": "allow"}],
            geo_allowed=None,
        ),
    )

    client = TestClient(app, client=("10.2.3.4", 50000))
    client.app.state.geoip_service = GeoService()
    resp = client.get("/health", headers={"Host": "ipgeo.local"})

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
