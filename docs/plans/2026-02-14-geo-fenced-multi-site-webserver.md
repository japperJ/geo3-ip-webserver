# Geo-Fenced Multi-Site Webserver Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a FastAPI-based multi-site webserver with per-site IP/GPS access control, admin UI, audit logs, and proof artifacts.

**Architecture:** Single FastAPI service with hostname-based routing for public traffic, admin API with JWT + RBAC, Postgres/PostGIS for data + geofence queries, Playwright worker for artifacts, S3-compatible storage.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Postgres + PostGIS, PyJWT, Passlib, Leaflet, React + Vite, Playwright, MinIO/S3.

---

### Task 1: Repo scaffold and baseline config

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/settings.py`
- Create: `backend/app/logging.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/health.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `infra/docker-compose.yml`
- Create: `.gitignore`

**Step 1: Write the failing test**

```python
# backend/tests/test_health.py
def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_health.py::test_health_ok -v`

Expected: FAIL (no app/client fixture)

**Step 3: Write minimal implementation**

```python
# backend/app/main.py
from fastapi import FastAPI
from app.routers.health import router as health_router

app = FastAPI()
app.include_router(health_router)

# backend/app/routers/health.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_health.py::test_health_ok -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend frontend infra .gitignore
git commit -m "chore: scaffold backend and frontend"
```

---

### Task 2: Database models and migrations (core entities)

**Files:**
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/models/user.py`
- Create: `backend/app/db/models/site.py`
- Create: `backend/app/db/models/site_user.py`
- Create: `backend/app/db/models/geofence.py`
- Create: `backend/app/db/models/ip_rule.py`
- Create: `backend/app/db/models/audit.py`
- Create: `backend/app/db/models/artifact.py`
- Create: `backend/app/db/models/ip_geo_cache.py`
- Create: `backend/migrations/versions/0001_core_tables.py`

**Step 1: Write the failing test**

```python
def test_site_defaults(db_session):
    site = Site(name="demo", hostname="demo.local", owner_user_id=uuid4())
    db_session.add(site); db_session.commit()
    assert site.filter_mode == "disabled"
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_models.py::test_site_defaults -v`

Expected: FAIL (models/migrations missing)

**Step 3: Write minimal implementation**

```python
# backend/app/db/models/site.py
class Site(Base):
    __tablename__ = "sites"
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
    hostname = Column(Text, unique=True)
    owner_user_id = Column(UUID, nullable=False)
    filter_mode = Column(Text, nullable=False, default="disabled")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Include PostGIS geometry columns for geofence and indexes.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_models.py::test_site_defaults -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/db backend/migrations
git commit -m "feat: add core database models and migration"
```

---

### Task 3: JWT auth + RBAC

**Files:**
- Create: `backend/app/auth/jwt.py`
- Create: `backend/app/auth/passwords.py`
- Create: `backend/app/auth/deps.py`
- Create: `backend/app/rbac/permissions.py`
- Modify: `backend/app/main.py`
- Create: `backend/app/routers/auth.py`

**Step 1: Write the failing test**

```python
def test_login_returns_tokens(client, user_factory):
    user = user_factory(password="secret")
    resp = client.post("/api/auth/login", json={"email": user.email, "password": "secret"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_auth.py::test_login_returns_tokens -v`

Expected: FAIL (no auth endpoints)

**Step 3: Write minimal implementation**

Implement JWT issuance, password hashing, login endpoint, and dependency for `current_user`.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_auth.py::test_login_returns_tokens -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/auth backend/app/routers/auth.py
git commit -m "feat: add JWT auth and login endpoint"
```

---

### Task 4: Access evaluation logic (IP rules + geofence)

**Files:**
- Create: `backend/app/access/ip_rules.py`
- Create: `backend/app/access/geofence.py`
- Create: `backend/app/access/decision.py`
- Create: `backend/tests/test_access_ip_rules.py`
- Create: `backend/tests/test_access_geofence.py`

**Step 1: Write the failing test**

```python
def test_ip_cidr_allow():
    rules = [IpRule(cidr="203.0.113.0/24", action="allow")]
    assert evaluate_ip_rules(rules, "203.0.113.5") is True
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_access_ip_rules.py::test_ip_cidr_allow -v`

Expected: FAIL

**Step 3: Write minimal implementation**

Use `ipaddress` stdlib for CIDR checks; for geofence, use PostGIS query helpers or shapely (avoid if possible).

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_access_ip_rules.py::test_ip_cidr_allow -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/access backend/tests/test_access_*
git commit -m "feat: add access evaluation logic"
```

---

### Task 5: IP geolocation with cache

**Files:**
- Create: `backend/app/geoip/service.py`
- Create: `backend/app/geoip/cache.py`
- Modify: `backend/app/settings.py`

**Step 1: Write the failing test**

```python
def test_geoip_cache_hit(geoip_service, ip_geo_cache):
    ip_geo_cache.store("203.0.113.5", {"country":"US"})
    result = geoip_service.lookup("203.0.113.5")
    assert result["country"] == "US"
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_geoip_cache.py::test_geoip_cache_hit -v`

Expected: FAIL

**Step 3: Write minimal implementation**

Implement DB-backed cache with TTL; fallback to MaxMind reader.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_geoip_cache.py::test_geoip_cache_hit -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/geoip backend/tests/test_geoip_cache.py
git commit -m "feat: add GeoIP lookup with cache"
```

---

### Task 6: Public access middleware + block page

**Files:**
- Create: `backend/app/middleware/access_gate.py`
- Create: `backend/app/templates/block.html`
- Modify: `backend/app/main.py`

**Step 1: Write the failing test**

```python
def test_blocked_request_returns_403(client, site_factory):
    site = site_factory(filter_mode="ip")
    resp = client.get("/", headers={"Host": site.hostname})
    assert resp.status_code == 403
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_access_gate.py::test_blocked_request_returns_403 -v`

Expected: FAIL

**Step 3: Write minimal implementation**

Access gate middleware that evaluates filter mode; returns block page on deny.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_access_gate.py::test_blocked_request_returns_403 -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/middleware backend/app/templates
git commit -m "feat: add access gate middleware and block page"
```

---

### Task 7: Audit logging + CSV export

**Files:**
- Create: `backend/app/audit/service.py`
- Create: `backend/app/routers/audit.py`
- Create: `backend/tests/test_audit.py`

**Step 1: Write the failing test**

```python
def test_audit_log_created_on_block(audit_service):
    entry = audit_service.log_block(site_id, "203.0.113.5", "geo blocked")
    assert entry.decision == "blocked"
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_audit.py::test_audit_log_created_on_block -v`

Expected: FAIL

**Step 3: Write minimal implementation**

Create audit records; add CSV export endpoint.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_audit.py::test_audit_log_created_on_block -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/audit backend/app/routers/audit.py
git commit -m "feat: add audit logging and export"
```

---

### Task 8: Artifact capture worker

**Files:**
- Create: `backend/app/artifacts/worker.py`
- Create: `backend/app/artifacts/storage.py`
- Create: `backend/tests/test_artifacts.py`

**Step 1: Write the failing test**

```python
def test_artifact_record_created(artifact_service):
    artifact = artifact_service.record(site_id, audit_id, "s3://bucket/key.png")
    assert artifact.path.endswith(".png")
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_artifacts.py::test_artifact_record_created -v`

Expected: FAIL

**Step 3: Write minimal implementation**

Implement Playwright capture in a background task; store in S3/MinIO.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_artifacts.py::test_artifact_record_created -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/artifacts backend/tests/test_artifacts.py
git commit -m "feat: add artifact capture and storage"
```

---

### Task 9: Admin API (sites, geofences, ip rules, roles)

**Files:**
- Create: `backend/app/routers/sites.py`
- Create: `backend/app/routers/geofences.py`
- Create: `backend/app/routers/ip_rules.py`
- Create: `backend/app/routers/site_users.py`
- Create: `backend/tests/test_admin_sites.py`

**Step 1: Write the failing test**

```python
def test_create_site(admin_client):
    resp = admin_client.post("/api/admin/sites", json={"name":"A","hostname":"a.local"})
    assert resp.status_code == 201
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_admin_sites.py::test_create_site -v`

Expected: FAIL

**Step 3: Write minimal implementation**

CRUD endpoints with RBAC; validate filter_mode.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_admin_sites.py::test_create_site -v`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/routers backend/tests/test_admin_sites.py
git commit -m "feat: add admin CRUD for sites and rules"
```

---

### Task 10: Frontend admin UI (React + Leaflet)

**Files:**
- Create: `frontend/src/pages/Sites.tsx`
- Create: `frontend/src/pages/SiteDetail.tsx`
- Create: `frontend/src/components/MapFenceEditor.tsx`
- Create: `frontend/src/components/IpRulesEditor.tsx`
- Create: `frontend/src/components/AuditLog.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Write the failing test**

```tsx
// frontend/src/__tests__/site-detail.test.tsx
it("renders map editor", () => {
  render(<SiteDetail />);
  expect(screen.getByText(/geofence/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- site-detail`

Expected: FAIL

**Step 3: Write minimal implementation**

Leaflet map with rectangle draw -> polygon saved to API.
Simple tables for IP rules, logs, and role management.

**Step 4: Run test to verify it passes**

Run: `npm test -- site-detail`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src
git commit -m "feat: add admin UI with Leaflet geofence editor"
```

---

### Task 11: Integration + E2E tests

**Files:**
- Create: `tests/e2e/blocked-allowed.spec.ts`
- Create: `tests/e2e/artifact.spec.ts`

**Step 1: Write the failing test**

```ts
test("blocks outside geofence", async ({ page }) => {
  await page.goto("http://site.local/");
  await expect(page).toHaveText(/blocked/i);
});
```

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/e2e/blocked-allowed.spec.ts`

Expected: FAIL

**Step 3: Write minimal implementation**

Use test fixtures to create site + geofence and simulate GPS header.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/e2e/blocked-allowed.spec.ts`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/e2e
git commit -m "test: add Playwright e2e coverage"
```

---

### Task 12: Docker + README

**Files:**
- Create: `Dockerfile`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Modify: `infra/docker-compose.yml`
- Create: `README.md`

**Step 1: Write the failing test**

```bash
# manual check
docker compose up --build
```

**Step 2: Run to verify it fails**

Expected: FAIL until dockerfiles exist

**Step 3: Write minimal implementation**

Add containers for api, db (PostGIS), minio, frontend.

**Step 4: Run to verify it passes**

Expected: services start; `/health` returns OK.

**Step 5: Commit**

```bash
git add Dockerfile backend/Dockerfile frontend/Dockerfile infra/docker-compose.yml README.md
git commit -m "docs: add docker setup and deployment notes"
```
