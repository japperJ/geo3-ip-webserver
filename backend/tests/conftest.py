import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
