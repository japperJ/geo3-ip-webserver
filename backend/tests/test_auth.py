from fastapi.testclient import TestClient

from app.auth.security import hash_password
from app.auth.store import add_user, clear_users
from app.main import app


def test_login_returns_tokens():
    clear_users()
    add_user("user@example.com", hash_password("secret"))

    client = TestClient(app)
    resp = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "secret"},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
