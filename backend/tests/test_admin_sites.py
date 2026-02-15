import os
from uuid import uuid4

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-should-be-at-least-32-characters")

from app.admin_store import clear_admin_store
from app.auth.security import hash_password
from app.auth.store import add_user, clear_users
from app.db.models.ip_rule import IPRuleAction
from app.db.models.site import SiteFilterMode
from app.db.models.site_user import SiteUserRole
from app.main import app


def _auth_headers(client: TestClient, role: str) -> dict[str, str]:
    clear_users()
    add_user("admin@example.com", hash_password("secret"), role=role)
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "secret"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_site(client: TestClient, headers: dict[str, str]) -> str:
    payload = {
        "name": "Site A",
        "hostname": "a.local",
        "owner_user_id": str(uuid4()),
    }
    resp = client.post("/api/admin/sites", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def _reset_state() -> None:
    clear_admin_store(app)
    clear_users()


def test_admin_sites_crud():
    _reset_state()
    client = TestClient(app)
    headers = _auth_headers(client, role="admin")

    payload = {
        "name": "Site A",
        "hostname": "a.local",
        "owner_user_id": str(uuid4()),
    }
    resp = client.post("/api/admin/sites", json=payload, headers=headers)
    assert resp.status_code == 201
    site_id = resp.json()["id"]

    resp = client.get("/api/admin/sites", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.patch(
        f"/api/admin/sites/{site_id}",
        json={"name": "Site B", "filter_mode": SiteFilterMode.IP.value},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Site B"
    assert resp.json()["filter_mode"] == SiteFilterMode.IP.value

    resp = client.delete(f"/api/admin/sites/{site_id}", headers=headers)
    assert resp.status_code == 204

    resp = client.get("/api/admin/sites", headers=headers)
    assert resp.json() == []


def test_admin_sites_unique_hostname_conflict():
    _reset_state()
    client = TestClient(app)
    headers = _auth_headers(client, role="admin")

    payload = {
        "name": "Site A",
        "hostname": "a.local",
        "owner_user_id": str(uuid4()),
    }
    resp = client.post("/api/admin/sites", json=payload, headers=headers)
    assert resp.status_code == 201
    resp = client.post("/api/admin/sites", json=payload, headers=headers)
    assert resp.status_code == 409


def test_admin_geofences_create_list():
    _reset_state()
    client = TestClient(app)
    headers = _auth_headers(client, role="owner")
    site_id = _create_site(client, headers)

    payload = {
        "name": "Fence",
        "polygon": [[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [-1.0, 1.0]],
    }
    resp = client.post(
        f"/api/admin/sites/{site_id}/geofences",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201

    resp = client.get(f"/api/admin/sites/{site_id}/geofences", headers=headers)
    assert resp.status_code == 200
    fences = resp.json()
    assert len(fences) == 1
    assert fences[0]["name"] == "Fence"


def test_admin_ip_rules_create_list():
    _reset_state()
    client = TestClient(app)
    headers = _auth_headers(client, role="owner")
    site_id = _create_site(client, headers)

    payload = {"cidr": "203.0.113.0/24", "action": IPRuleAction.ALLOW.value}
    resp = client.post(
        f"/api/admin/sites/{site_id}/ip-rules",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201

    resp = client.get(f"/api/admin/sites/{site_id}/ip-rules", headers=headers)
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 1
    assert rules[0]["cidr"] == "203.0.113.0/24"


def test_admin_site_users_add_remove():
    _reset_state()
    client = TestClient(app)
    headers = _auth_headers(client, role="admin")
    site_id = _create_site(client, headers)
    user_id = str(uuid4())

    payload = {"user_id": user_id, "role": SiteUserRole.VIEWER.value}
    resp = client.post(
        f"/api/admin/sites/{site_id}/users",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201

    resp = client.delete(
        f"/api/admin/sites/{site_id}/users/{user_id}",
        headers=headers,
    )
    assert resp.status_code == 204


def test_admin_requires_owner_or_admin():
    _reset_state()
    client = TestClient(app)
    headers = _auth_headers(client, role="viewer")

    resp = client.post(
        "/api/admin/sites",
        json={"name": "Site A", "hostname": "a.local", "owner_user_id": str(uuid4())},
        headers=headers,
    )
    assert resp.status_code == 403


def test_repository_imports():
    from app.admin.repositories.site_repository import SiteRepository
    from app.admin.repositories.geofence_repository import GeofenceRepository
    from app.admin.repositories.ip_rule_repository import IPRuleRepository
    from app.admin.repositories.site_user_repository import SiteUserRepository

    assert SiteRepository and GeofenceRepository and IPRuleRepository and SiteUserRepository
