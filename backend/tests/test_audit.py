import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-should-be-at-least-32-characters")

from app.audit import service as audit_service
from app.main import app


def test_log_block_records_and_exports_csv():
    audit_service.clear()

    audit_service.log_block(
        site_id="site-123",
        client_ip="203.0.113.5",
        ip_geo_country="US",
        reason="blocked",
        artifact_path="/tmp/artifact",
    )

    csv_data = audit_service.export_csv()
    lines = csv_data.strip().splitlines()

    assert lines[0] == "timestamp,site_id,client_ip,ip_geo_country,decision,reason,artifact_path"
    assert len(lines) == 2
    assert "site-123" in lines[1]
    assert "203.0.113.5" in lines[1]
    assert "US" in lines[1]
    assert "blocked" in lines[1]


def test_audit_export_endpoint_returns_csv():
    audit_service.clear()
    audit_service.log_block(
        site_id="site-123",
        client_ip="203.0.113.5",
        ip_geo_country="US",
        reason="blocked",
        artifact_path=None,
    )

    client = TestClient(app)
    resp = client.get("/audit/export")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "site-123" in resp.text
