# Phase 1 Persisted Admin APIs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace in-memory admin stores with SQLAlchemy-backed repositories and keep the access-gate registry fresh after admin writes.

**Architecture:** Introduce a thin repository layer wrapping the request-scoped SQLAlchemy session, then update admin routers to use repositories and return JSON-safe dicts. Add registry refresh/invalidation helpers in access-gate middleware and ensure tests run with DB-backed fixtures.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, Alembic, GeoAlchemy2 (PostGIS)

---

## Dependencies and Assumptions

- Phase 0 must be complete: DB engine/session wiring, Alembic migrations applied, PostGIS enabled, and models registered in `backend/app/db/models/__init__.py`.
- Uniqueness constraints exist for `Site.hostname` and `(site_id, user_id)` on site users; repository tests depend on these to surface IntegrityError.
- Access-gate registry rebuild can run inside the app process using DB reads (no external cache invalidation required for Phase 1).

## Requirement-to-Task Mapping

| Requirement (Phase 1) | Tasks |
| --- | --- |
| Persist sites, geofences, IP rules, site users in Postgres | 2, 3, 4 |
| Admin APIs for CRUD on those entities using DB persistence | 5 |
| Keep API behavior stable or update tests to match persistence | 5, 7 |
| Cache invalidation on updates to keep access-gate latency low | 6 |

### Task 1: Add repository scaffolding and shared helpers

**Files:**
- Create: `backend/app/admin/repositories/__init__.py`
- Create: `backend/app/admin/repositories/site_repository.py`
- Create: `backend/app/admin/repositories/geofence_repository.py`
- Create: `backend/app/admin/repositories/ip_rule_repository.py`
- Create: `backend/app/admin/repositories/site_user_repository.py`
- Create: `backend/app/admin/repositories/serialization.py`
- Modify: `backend/app/db/models/__init__.py`

**Step 1: Write the failing test**

Create a minimal unit test that imports each repository module to ensure module paths are correct.

```python
def test_repository_imports():
    from app.admin.repositories.site_repository import SiteRepository
    from app.admin.repositories.geofence_repository import GeofenceRepository
    from app.admin.repositories.ip_rule_repository import IPRuleRepository
    from app.admin.repositories.site_user_repository import SiteUserRepository
    assert SiteRepository and GeofenceRepository and IPRuleRepository and SiteUserRepository
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_admin_sites.py::test_repository_imports -v`
Expected: FAIL with ImportError (modules missing)

**Step 3: Write minimal implementation**

Create repository modules with empty class stubs and shared serialization helpers in `serialization.py`.

```python
class SiteRepository:
    def __init__(self, db: Session) -> None:
        self._db = db
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_admin_sites.py::test_repository_imports -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/admin/repositories backend/tests/test_admin_sites.py
git commit -m "test: add repository scaffolding"
```

### Task 2: Implement SiteRepository CRUD with unique hostname handling

**Files:**
- Modify: `backend/app/admin/repositories/site_repository.py`
- Modify: `backend/app/admin/repositories/serialization.py`
- Modify: `backend/app/db/models/__init__.py`
- Test: `backend/tests/test_admin_sites.py`

**Step 1: Write the failing test**

Add tests that create a site, list sites, update fields, and enforce unique hostname conflicts returning 409 from the router layer.

```python
def test_admin_sites_unique_hostname_conflict(client, admin_headers):
    payload = {"name": "A", "hostname": "a.local", "owner_user_id": str(uuid4())}
    assert client.post("/api/admin/sites", json=payload, headers=admin_headers).status_code == 201
    resp = client.post("/api/admin/sites", json=payload, headers=admin_headers)
    assert resp.status_code == 409
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_sites_unique_hostname_conflict -v`
Expected: FAIL with status_code != 409

**Step 3: Write minimal implementation**

Implement repository methods:

```python
class SiteRepository:
    def create(self, payload: SiteCreate) -> Site:
        site = Site(
            name=payload.name,
            hostname=payload.hostname,
            owner_user_id=payload.owner_user_id,
            filter_mode=payload.filter_mode or SiteFilterMode.DISABLED,
        )
        self._db.add(site)
        self._db.flush()
        return site

    def list_all(self) -> list[Site]:
        return list(self._db.query(Site).all())

    def get(self, site_id: str) -> Site | None:
        return self._db.get(Site, site_id)

    def update(self, site: Site, payload: SiteUpdate) -> Site:
        if payload.name is not None:
            site.name = payload.name
        if payload.hostname is not None:
            site.hostname = payload.hostname
        if payload.filter_mode is not None:
            site.filter_mode = payload.filter_mode
        self._db.flush()
        return site

    def delete(self, site: Site) -> None:
        self._db.delete(site)
```

In the router layer, catch IntegrityError for duplicate hostnames and return 409.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_sites_unique_hostname_conflict -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/admin/repositories/site_repository.py backend/app/admin/repositories/serialization.py backend/tests/test_admin_sites.py
git commit -m "feat: add site repository with uniqueness handling"
```

### Task 3: Implement GeofenceRepository with geometry conversion

**Files:**
- Modify: `backend/app/admin/repositories/geofence_repository.py`
- Modify: `backend/app/admin/repositories/serialization.py`
- Modify: `backend/app/routers/geofences.py`
- Test: `backend/tests/test_admin_sites.py`

**Step 1: Write the failing test**

Add a test that creates a geofence and asserts that polygon/center fields round-trip as lists in JSON.

```python
def test_admin_geofences_round_trip(client, owner_headers, site_id):
    payload = {"name": "Fence", "polygon": [[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [-1.0, 1.0]]}
    resp = client.post(f"/api/admin/sites/{site_id}/geofences", json=payload, headers=owner_headers)
    assert resp.status_code == 201
    assert resp.json()["polygon"] == payload["polygon"]
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_geofences_round_trip -v`
Expected: FAIL with serialization error or None polygon

**Step 3: Write minimal implementation**

Use GeoAlchemy2 WKTElement for writes and ST_AsGeoJSON for reads in the repository. Implement helpers in `serialization.py`:

```python
def polygon_to_wkt(polygon: list[list[float]] | None) -> WKTElement | None:
    # Build POLYGON((lng lat, ...)) and return WKTElement
```

And in repository, select geofences using `func.ST_AsGeoJSON(Geofence.polygon)` and parse JSON to lists.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_geofences_round_trip -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/admin/repositories/geofence_repository.py backend/app/admin/repositories/serialization.py backend/app/routers/geofences.py backend/tests/test_admin_sites.py
git commit -m "feat: add geofence repository with geometry serialization"
```

### Task 4: Implement IPRuleRepository and SiteUserRepository

**Files:**
- Modify: `backend/app/admin/repositories/ip_rule_repository.py`
- Modify: `backend/app/admin/repositories/site_user_repository.py`
- Modify: `backend/app/routers/ip_rules.py`
- Modify: `backend/app/routers/site_users.py`
- Test: `backend/tests/test_admin_sites.py`

**Step 1: Write the failing test**

Add tests that confirm IP rules return enum values and site users avoid duplicates for (site_id, user_id).

```python
def test_admin_site_users_no_duplicate(client, admin_headers, site_id):
    payload = {"user_id": str(uuid4()), "role": SiteUserRole.VIEWER.value}
    assert client.post(f"/api/admin/sites/{site_id}/users", json=payload, headers=admin_headers).status_code == 201
    resp = client.post(f"/api/admin/sites/{site_id}/users", json=payload, headers=admin_headers)
    assert resp.status_code in (200, 409)
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_site_users_no_duplicate -v`
Expected: FAIL with unexpected status

**Step 3: Write minimal implementation**

Implement repository methods to list/create IP rules and list/create/delete site users. Use `db.flush()` after add to populate IDs. If `(site_id, user_id)` exists, return existing entry or raise an integrity error that the router maps to 409.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_site_users_no_duplicate -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/admin/repositories/ip_rule_repository.py backend/app/admin/repositories/site_user_repository.py backend/app/routers/ip_rules.py backend/app/routers/site_users.py backend/tests/test_admin_sites.py
git commit -m "feat: add ip rule and site user repositories"
```

### Task 5: Update admin routers to use repositories and serialize responses

**Files:**
- Modify: `backend/app/routers/sites.py`
- Modify: `backend/app/routers/geofences.py`
- Modify: `backend/app/routers/ip_rules.py`
- Modify: `backend/app/routers/site_users.py`
- Modify: `backend/app/admin_store.py`
- Test: `backend/tests/test_admin_sites.py`

**Step 1: Write the failing test**

Update tests to remove use of `clear_admin_store` and assert JSON responses return string IDs and enum values.

```python
def test_admin_sites_crud(client, admin_headers):
    resp = client.post("/api/admin/sites", json=payload, headers=admin_headers)
    assert isinstance(resp.json()["id"], str)
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_sites_crud -v`
Expected: FAIL with missing fixtures or old in-memory behavior

**Step 3: Write minimal implementation**

Refactor routers to:

- Instantiate repositories with `db` from `get_db()`.
- Use repository methods and serialize responses via helpers (e.g., `site_to_dict`, `ip_rule_to_dict`, `geofence_to_dict`, `site_user_to_dict`).
- Map IntegrityError to 409 and missing records to 404.
- Keep response payload shape identical to current tests (string IDs, enum values).

Consider deleting or stubbing `admin_store` usage if no longer needed.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_admin_sites.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/routers backend/app/admin_store.py backend/tests/test_admin_sites.py
git commit -m "feat: move admin routers to db-backed repositories"
```

### Task 6: Add access-gate registry refresh hooks after admin writes

**Files:**
- Modify: `backend/app/middleware/access_gate.py`
- Modify: `backend/app/routers/sites.py`
- Modify: `backend/app/routers/geofences.py`
- Modify: `backend/app/routers/ip_rules.py`

**Step 1: Write the failing test**

Add a test that updates a site’s filter mode and ensures access-gate registry refresh logic is called (use a mock or spy in app state).

```python
def test_admin_updates_refresh_registry(monkeypatch, client, admin_headers, site_id):
    called = {"value": False}
    def refresh(_db, _app):
        called["value"] = True
    monkeypatch.setattr("app.middleware.access_gate.refresh_site_registry", refresh)
    client.patch(f"/api/admin/sites/{site_id}", json={"filter_mode": "ip"}, headers=admin_headers)
    assert called["value"] is True
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_updates_refresh_registry -v`
Expected: FAIL (refresh not called)

**Step 3: Write minimal implementation**

In `access_gate.py`, add:

- `refresh_site_registry(db: Session, app: FastAPI)` that clears and rebuilds `SiteConfigRegistry` from DB.
- Helper to register per-site config with IP rules and geo flags (use repository or query directly).

Call `refresh_site_registry` after create/update/delete of sites and after geofence/ip rule writes.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_admin_sites.py::test_admin_updates_refresh_registry -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/middleware/access_gate.py backend/app/routers
git commit -m "feat: refresh site registry after admin writes"
```

### Task 7: Convert admin tests to DB-backed fixtures

**Files:**
- Create: `backend/tests/conftest.py`
- Modify: `backend/tests/test_admin_sites.py`

**Step 1: Write the failing test**

Add fixtures for DB setup/teardown and update tests to use `client`, `admin_headers`, `owner_headers`, and `site_id` fixtures.

```python
@pytest.fixture
def site_id(client, admin_headers):
    resp = client.post("/api/admin/sites", json={...}, headers=admin_headers)
    return resp.json()["id"]
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_admin_sites.py -v`
Expected: FAIL with missing fixtures

**Step 3: Write minimal implementation**

Implement fixtures that:

- Use `TestClient(app)` once per test.
- Use a test database URL (if configured) and ensure DB cleanup between tests.
- Clear auth users via existing `clear_users()`.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_admin_sites.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_admin_sites.py
git commit -m "test: migrate admin tests to db fixtures"
```

### Task 8: Run full admin test suite and document any follow-ups

**Files:**
- Modify: `.planning/phases/1/PLAN.md`

**Pass/Fail Criteria:**

- Required green: `backend/tests/test_admin_sites.py`, `backend/tests/test_access_gate.py`, `backend/tests/test_access_geofence.py`, `backend/tests/test_access_ip_rules.py`.
- Pass only if all required tests are green with no skipped or xfailed cases tied to Phase 1 changes.
- Fail if any required test fails or is skipped; record each failure with error summary and next action.

**Step 1: Run admin-related tests**

Run: `pytest backend/tests/test_admin_sites.py -v`
Expected: PASS

**Step 2: Run broader suite**

Run: `pytest backend/tests/test_access_gate.py backend/tests/test_access_geofence.py backend/tests/test_access_ip_rules.py -v`
Expected: PASS

**Step 3: Document any gaps**

If any required test fails or is skipped, add a checklist at the end of this plan with:

- Test name and failure summary
- Likely cause (e.g., missing Phase 0 migration or mismatched response shape)
- Required follow-up task or link to issue

Do not proceed to execution until the checklist is empty or all items are explicitly accepted as follow-ups.

**Step 4: Commit**

```bash
git add .planning/phases/1/PLAN.md
git commit -m "docs: update phase 1 plan after test verification"
```

---

## Open Questions to Resolve Before Implementation
1. Should geofence payloads accept both polygon and circle in a single request, and if both are present which takes precedence?
2. Is a full registry rebuild after each admin write acceptable for Phase 1, or is targeted invalidation required?
3. Are soft deletes required for `Site` and related records, or is hard delete acceptable (current behavior is hard delete)?
