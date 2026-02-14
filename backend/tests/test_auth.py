import base64
import hashlib
import hmac
import json
import os
import time

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ.setdefault("JWT_SECRET", "test-secret-should-be-at-least-32-characters")

from app.auth.jwt import decode_jwt, encode_jwt
from app.auth.security import hash_password
from app.auth.store import add_user, clear_users
from app.main import app
from app.settings import Settings, settings


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


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


def test_settings_require_jwt_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ValidationError):
        Settings()


def test_settings_reject_short_jwt_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET", "short")

    with pytest.raises(ValidationError):
        Settings()


def test_login_rejects_invalid_credentials():
    clear_users()
    add_user("user@example.com", hash_password("secret"))

    client = TestClient(app)
    resp = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrong"},
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


def test_decode_jwt_rejects_expired_token():
    token = encode_jwt({"sub": "user@example.com", "exp": int(time.time()) - 10})

    assert decode_jwt(token) is None


def test_decode_jwt_rejects_invalid_signature():
    token = encode_jwt({"sub": "user@example.com", "exp": int(time.time()) + 60})
    header_b64, payload_b64, signature_b64 = token.split(".")
    replacement = "A" if signature_b64[-1] != "A" else "B"
    tampered = f"{header_b64}.{payload_b64}.{signature_b64[:-1]}{replacement}"

    assert decode_jwt(tampered) is None


def test_decode_jwt_rejects_mismatched_algorithm():
    header = {"alg": "HS512", "typ": "JWT"}
    payload = {"sub": "user@example.com", "exp": int(time.time()) + 60}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    signature_b64 = _b64url_encode(signature)
    token = f"{header_b64}.{payload_b64}.{signature_b64}"

    assert decode_jwt(token) is None
