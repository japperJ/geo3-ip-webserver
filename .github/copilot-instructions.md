# Copilot Instructions — geo3-ip-webserver

## Build, Test, and Lint

### Backend (Python — FastAPI)

```bash
cd backend

# Install (editable, from pyproject.toml)
pip install -e .

# Run the dev server
uvicorn app.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_access_gate.py

# Run a single test by name
pytest tests/test_access_gate.py -k "test_blocked_request_logs_audit"

# Lint (Ruff, configured in pyproject.toml, line-length 100)
ruff check .
```

### Frontend (React + TypeScript — Vite)

```bash
cd frontend
npm install
npm run dev      # dev server
npm run build    # typecheck + production build
```

### Infrastructure

```bash
cd infra
docker compose up        # API + Postgres/PostGIS + MinIO
```

The API container exposes port 8001. Postgres on 5433, MinIO API on 9002, MinIO console on 9003.

## Architecture

This is a **geo-fenced, multi-site access-control webserver**. The backend is the primary deliverable; the frontend is a placeholder.

### Request Flow

```
Client → AccessGateMiddleware → Router → Repository → PostgreSQL/PostGIS
                ↓ (on block)
         AuditService + ArtifactCapture → S3/MinIO
```

### Layers

- **Middleware** (`app/middleware/access_gate.py`): Intercepts every request. Uses a `SiteConfigRegistry` (cached in `app.state`) to evaluate access per site. Chains IP rule checks → GeoIP lookup → `decide_access()`.
- **Access logic** (`app/access/`): Pure functions. `decision.py` implements a decision matrix over `SiteFilterMode` (disabled / ip / geo / ip_and_geo). `geofence.py` and `ip_rules.py` handle individual checks.
- **Routers** (`app/routers/`): FastAPI routers for sites, geofences, IP rules, site users, auth, audit, health.
- **Repositories** (`app/admin/repositories/`): CRUD over SQLAlchemy models. Inject `Session` via FastAPI `Depends(get_db)`. Handle UUID coercion and GeoJSON ↔ WKT serialization for spatial data.
- **Models** (`app/db/models/`): SQLAlchemy 2.0 `Mapped` types with UUID primary keys, GeoAlchemy2 geometry columns (SRID 4326), and server-side timestamp defaults.
- **GeoIP** (`app/geoip/`): Two-tier cache (in-memory TTL → DB → MaxMind `.mmdb` reader). `GeoIPService.lookup()` returns `{country_code, latitude, longitude}`.
- **Artifacts** (`app/artifacts/`): `S3CompatibleStorage` wraps boto3 for MinIO/S3. Factory pattern in `storage_factory.py`. Stored URI format: `s3://bucket/key`.
- **Audit** (`app/audit/`): In-memory deque (capped at 1000). Logs block events with timestamp, site_id, client_ip, decision, artifact_path. Exports to CSV.
- **Auth** (`app/auth/`): JWT (HS256) via `pydantic-settings`. `get_current_user()` and `require_admin()` as FastAPI dependencies. Role-based: admin / owner / site user.

### Configuration

All config via environment variables, loaded through `pydantic-settings` in `app/settings.py`. See `.env.example` for the full list. `JWT_SECRET` must be ≥32 chars.

### Database

- PostgreSQL with PostGIS extension, managed by Alembic migrations in `backend/migrations/`.
- `app/db/session.py`: `SessionLocal` factory with `pool_pre_ping=True`, `autoflush=False`. `get_db()` yields a session with auto-commit/rollback.
- Migration commands: `alembic upgrade head`, `alembic revision --autogenerate -m "description"`.

### In-Memory Fallback

`app/admin_store.py` provides an in-memory dict-based store used during testing and before DB persistence was wired. Tests use this + spy/mock objects attached to `app.state`.

## Conventions

### Test Patterns

- No shared `conftest.py` yet — each test file sets `os.environ.setdefault("JWT_SECRET", ...)` before importing app modules.
- Integration tests use `TestClient(app)` from FastAPI.
- Spy pattern: custom classes with `.calls` lists (e.g., `AuditSpy`, `CaptureSpy`) injected into `app.state`.
- Test isolation: `clear_admin_store(app)` resets in-memory state between tests.

### Development Workflow (from planning docs)

The project follows a phased roadmap (see `.planning/ROADMAP.md`). Each phase uses a write-test → run-test → implement → commit cycle. Phase status is tracked in `.planning/STATE.md`.

### Code Style

- Ruff linter with 100-char line length.
- SQLAlchemy 2.0 style: `Mapped[T]`, `mapped_column()`, type annotations everywhere.
- Pydantic v2 for settings and request/response schemas.
- FastAPI dependency injection via `Depends()` for DB sessions, auth, and permissions.
