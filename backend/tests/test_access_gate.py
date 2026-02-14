import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-should-be-at-least-32-characters")

from app.db.models.site import SiteFilterMode
from app.main import app
from app.middleware.access_gate import SiteAccessConfig, clear_site_configs, register_site_config


def test_blocked_request_returns_403():
    clear_site_configs()
    register_site_config(
        "blocked.local",
        SiteAccessConfig(filter_mode=SiteFilterMode.IP, ip_rules=[]),
    )

    client = TestClient(app)
    resp = client.get("/", headers={"Host": "blocked.local"})

    assert resp.status_code == 403
