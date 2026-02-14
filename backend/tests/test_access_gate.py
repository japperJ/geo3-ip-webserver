import os

import pytest

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-should-be-at-least-32-characters")

from app.db.models.site import SiteFilterMode
from app.main import app
from app.middleware.access_gate import SiteAccessConfig, clear_site_configs, register_site_config


def _setup_site_config(hostname: str, config: SiteAccessConfig) -> None:
    clear_site_configs(app)
    register_site_config(app, hostname, config)


def test_blocked_request_returns_403_and_records_artifact():
    class AuditSpy:
        def __init__(self) -> None:
            self.calls = []

        def log_block(
            self,
            *,
            site_id: str,
            client_ip: str | None = None,
            ip_geo_country: str | None = None,
            reason: str | None = None,
            artifact_path: str | None = None,
        ) -> None:
            self.calls.append(
                {
                    "site_id": site_id,
                    "client_ip": client_ip,
                    "ip_geo_country": ip_geo_country,
                    "reason": reason,
                    "artifact_path": artifact_path,
                }
            )

    class CaptureSpy:
        def __init__(self) -> None:
            self.calls = []

        def capture(self, site_id) -> str:
            self.calls.append(site_id)
            return f"s3://bucket/{site_id}/artifact"

    audit_spy = AuditSpy()
    capture_spy = CaptureSpy()
    app.state.audit_service = audit_spy
    app.state.capture_service = capture_spy
    site_id = "11111111-1111-1111-1111-111111111111"

    _setup_site_config(
        "blocked.local",
        SiteAccessConfig(site_id=site_id, filter_mode=SiteFilterMode.IP, ip_rules=[]),
    )

    client = TestClient(app, client=("10.1.2.3", 50000))
    resp = client.get("/", headers={"Host": "blocked.local"})

    assert resp.status_code == 403
    assert capture_spy.calls == [site_id]
    assert audit_spy.calls == [
        {
            "site_id": site_id,
            "client_ip": "10.1.2.3",
            "ip_geo_country": None,
            "reason": "blocked",
            "artifact_path": f"s3://bucket/{site_id}/artifact",
        }
    ]


def test_allowed_request_allows_ip_match():
    _setup_site_config(
        "allowed.local",
        SiteAccessConfig(
            site_id="22222222-2222-2222-2222-222222222222",
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
        SiteAccessConfig(
            site_id="33333333-3333-3333-3333-333333333333",
            filter_mode=SiteFilterMode.GEO,
            ip_rules=[],
            geo_allowed=None,
        ),
    )

    client = TestClient(app, client=("203.0.113.10", 50000))
    client.app.state.geoip_service = GeoService()
    resp = client.get("/health", headers={"Host": "geo.local"})

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.parametrize("geo_result", [None, {}])
def test_geo_blocks_when_geoip_lookup_returns_falsey(geo_result):
    class GeoService:
        def lookup(self, ip: str):
            return geo_result

    _setup_site_config(
        "geo-falsey.local",
        SiteAccessConfig(
            site_id="44444444-4444-4444-4444-444444444444",
            filter_mode=SiteFilterMode.GEO,
            ip_rules=[],
            geo_allowed=None,
        ),
    )

    client = TestClient(app, client=("203.0.113.11", 50000))
    client.app.state.geoip_service = GeoService()
    resp = client.get("/health", headers={"Host": "geo-falsey.local"})

    assert resp.status_code == 403


def test_ip_and_geo_requires_both_allow_and_geo():
    class GeoService:
        def lookup(self, ip: str):
            return True

    _setup_site_config(
        "ipgeo.local",
        SiteAccessConfig(
            site_id="55555555-5555-5555-5555-555555555555",
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


@pytest.mark.parametrize("geo_result", [None, {}])
def test_ip_and_geo_blocks_when_geoip_lookup_returns_falsey(geo_result):
    class GeoService:
        def lookup(self, ip: str):
            return geo_result

    _setup_site_config(
        "ipgeo-falsey.local",
        SiteAccessConfig(
            site_id="66666666-6666-6666-6666-666666666666",
            filter_mode=SiteFilterMode.IP_AND_GEO,
            ip_rules=[{"cidr": "10.2.3.5/32", "action": "allow"}],
            geo_allowed=None,
        ),
    )

    client = TestClient(app, client=("10.2.3.5", 50000))
    client.app.state.geoip_service = GeoService()
    resp = client.get("/health", headers={"Host": "ipgeo-falsey.local"})

    assert resp.status_code == 403


def test_blocked_request_handles_capture_failure():
    class AuditSpy:
        def __init__(self) -> None:
            self.calls = []

        def log_block(
            self,
            *,
            site_id: str,
            client_ip: str | None = None,
            ip_geo_country: str | None = None,
            reason: str | None = None,
            artifact_path: str | None = None,
        ) -> None:
            self.calls.append(
                {
                    "site_id": site_id,
                    "client_ip": client_ip,
                    "ip_geo_country": ip_geo_country,
                    "reason": reason,
                    "artifact_path": artifact_path,
                }
            )

    class CaptureSpy:
        def capture(self, site_id) -> str:
            raise RuntimeError("capture failed")

    audit_spy = AuditSpy()
    app.state.audit_service = audit_spy
    app.state.capture_service = CaptureSpy()
    site_id = "77777777-7777-7777-7777-777777777777"

    _setup_site_config(
        "blocked-failure.local",
        SiteAccessConfig(site_id=site_id, filter_mode=SiteFilterMode.IP, ip_rules=[]),
    )

    client = TestClient(app, client=("10.9.9.9", 50000))
    resp = client.get("/", headers={"Host": "blocked-failure.local"})

    assert resp.status_code == 403
    assert audit_spy.calls == [
        {
            "site_id": site_id,
            "client_ip": "10.9.9.9",
            "ip_geo_country": None,
            "reason": "blocked",
            "artifact_path": None,
        }
    ]
