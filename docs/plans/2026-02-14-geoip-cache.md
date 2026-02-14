# GeoIP Cache Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add GeoIP lookup with in-memory and DB-backed cache plus settings and tests for cache hits.

**Architecture:** Introduce a GeoIP service that wraps a reader with a cache layer. The cache uses in-memory TTL entries and optionally persists to the existing `ip_geo_cache` table. Settings configure MaxMind DB path and cache TTL.

**Tech Stack:** FastAPI backend, SQLAlchemy models, pytest.

---

### Task 1: Add GeoIP settings

**Files:**
- Modify: `backend/app/settings.py`

**Step 1: Write the failing test**

```python
def test_settings_has_geoip_defaults():
    from app.settings import Settings

    settings = Settings(jwt_secret="x" * 32)
    assert settings.geoip_db_path
    assert settings.geoip_cache_ttl_seconds > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_geoip_cache.py::test_settings_has_geoip_defaults -v`
Expected: FAIL with attribute error for missing settings.

**Step 3: Write minimal implementation**

```python
geoip_db_path: str = "./GeoLite2-City.mmdb"
geoip_cache_ttl_seconds: int = 3600
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_geoip_cache.py::test_settings_has_geoip_defaults -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/settings.py backend/tests/test_geoip_cache.py
git commit -m "feat: add GeoIP settings"
```

### Task 2: Implement GeoIP cache module

**Files:**
- Create: `backend/app/geoip/cache.py`

**Step 1: Write the failing test**

```python
def test_geoip_cache_hit():
    from app.geoip.cache import GeoIPCache

    cache = GeoIPCache(ttl_seconds=60)
    cache.set("1.2.3.4", {"country_code": "US"})
    assert cache.get("1.2.3.4") == {"country_code": "US"}
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_geoip_cache.py::test_geoip_cache_hit -v`
Expected: FAIL with import error.

**Step 3: Write minimal implementation**

```python
class GeoIPCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, dict[str, object]]]

    def get(self, ip: str) -> dict[str, object] | None:
        ...

    def set(self, ip: str, data: dict[str, object]) -> None:
        ...
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_geoip_cache.py::test_geoip_cache_hit -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/geoip/cache.py backend/tests/test_geoip_cache.py
git commit -m "feat: add in-memory geoip cache"
```

### Task 3: Implement GeoIP service

**Files:**
- Create: `backend/app/geoip/service.py`

**Step 1: Write the failing test**

```python
def test_geoip_service_cache_hit():
    from app.geoip.cache import GeoIPCache
    from app.geoip.service import GeoIPService

    cache = GeoIPCache(ttl_seconds=60)
    cache.set("1.2.3.4", {"country_code": "US"})
    service = GeoIPService(cache=cache, reader=None)
    assert service.lookup("1.2.3.4") == {"country_code": "US"}
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_geoip_cache.py::test_geoip_service_cache_hit -v`
Expected: FAIL with import error.

**Step 3: Write minimal implementation**

```python
class GeoIPService:
    def __init__(self, cache: GeoIPCache, reader: object | None) -> None:
        self._cache = cache
        self._reader = reader

    def lookup(self, ip: str) -> dict[str, object] | None:
        cached = self._cache.get(ip)
        if cached is not None:
            return cached
        if self._reader is None:
            raise RuntimeError("MaxMind reader not available")
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_geoip_cache.py::test_geoip_service_cache_hit -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/geoip/service.py backend/tests/test_geoip_cache.py
git commit -m "feat: add geoip lookup service"
```

### Task 4: Add DB cache integration stub

**Files:**
- Modify: `backend/app/geoip/service.py`

**Step 1: Write the failing test**

```python
def test_geoip_service_uses_db_cache():
    from app.geoip.cache import GeoIPCache
    from app.geoip.service import GeoIPService

    class FakeSession:
        def __init__(self):
            self.calls = 0
        def query(self, model):
            self.calls += 1
            return []

    service = GeoIPService(cache=GeoIPCache(60), reader=None, db_session=FakeSession())
    with pytest.raises(RuntimeError):
        service.lookup("1.2.3.4")
    assert service.db_calls == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_geoip_cache.py::test_geoip_service_uses_db_cache -v`
Expected: FAIL with attribute error.

**Step 3: Write minimal implementation**

```python
class GeoIPService:
    def __init__(..., db_session: object | None = None):
        self._db_session = db_session
        self._db_calls = 0

    @property
    def db_calls(self) -> int:
        return self._db_calls

    def _fetch_from_db(self, ip: str) -> dict[str, object] | None:
        if self._db_session is None:
            return None
        self._db_calls += 1
        return None
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_geoip_cache.py::test_geoip_service_uses_db_cache -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/geoip/service.py backend/tests/test_geoip_cache.py
git commit -m "feat: add db cache hook for geoip"
```

### Task 5: Run full targeted tests

**Step 1: Run tests**

Run: `pytest backend/tests/test_geoip_cache.py -v`
Expected: PASS

**Step 2: Commit**

```bash
git add backend/tests/test_geoip_cache.py
git commit -m "test: verify geoip cache behavior"
```
