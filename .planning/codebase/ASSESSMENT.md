# Codebase Assessment

## Status Overview
The backend implements core access-control logic, admin APIs, and audit/artifact plumbing, but much of it is in-memory or stubbed and not wired to persistent storage. The frontend is a placeholder. Docker setup exists only for the API container.

## Implemented Features
- FastAPI app with access gate middleware and block page (`backend/app/main.py`, `backend/app/middleware/access_gate.py`, `backend/app/templates/block.html`).
- JWT auth with password hashing and login endpoint (`backend/app/auth/`).
- Admin APIs for sites, geofences, IP rules, and site users using an in-memory admin store (`backend/app/routers/*`, `backend/app/admin_store.py`).
- Access evaluation logic for IP rules, geofence math, and combined decisioning (`backend/app/access/`).
- GeoIP cache + service abstraction with in-memory cache and optional DB hook (`backend/app/geoip/`).
- Audit logging in-memory with CSV export (`backend/app/audit/service.py`, `backend/app/routers/audit.py`).
- Artifact capture worker + S3-compatible storage abstraction (`backend/app/artifacts/`).
- SQLAlchemy models and migration for core tables (`backend/app/db/models/*`, `backend/migrations/`).
- Tests covering auth, access gate, access logic, audit, geoip cache, admin APIs, artifacts, and model defaults (`backend/tests/*`).

## Gaps and Incomplete Areas
- **Persistence wiring:** Admin APIs operate on in-memory `AdminStore` instead of SQLAlchemy models; no DB session management or repository layer is present. No `backend/app/db/session.py` despite the plan, and no runtime configuration for DB engine/session.
- **Access gate integration:** The access middleware uses a hostname registry populated via `register_site_config`, but no runtime synchronization exists from DB/admin API to the registry. Site configs never get registered in production flows.
- **GeoIP + geofence enforcement:** Middleware only checks GeoIP truthiness, not actual geofence containment. Geofence data is not used in access decisions. There is no GPS header handling or PostGIS queries.
- **Audit persistence:** Audit logging is in-memory only; the `AccessAudit` model is not used. CSV export reads from memory, not DB.
- **Artifacts:** Capture uses a generic `capture_service` hook but no Playwright capture implementation is present. Artifact metadata is not stored (the helper exists but is not called in middleware).
- **RBAC and users:** Auth user store is in-memory; no user creation/admin endpoints or persistence. Site user roles are stored in-memory only.
- **Frontend:** `frontend/src/App.tsx` is a stub (“Geo3 Admin”). No pages, routing, API client, or map editor.
- **Infra/ops:** Docker Compose only starts the API container. No Postgres/PostGIS, no MinIO/S3, no frontend container, and no README.

## Placeholder or Stub Indicators
- In-memory stores for users and admin data (`backend/app/auth/store.py`, `backend/app/admin_store.py`).
- Optional `db_session` in GeoIP service that expects a custom `query` callable rather than SQLAlchemy session usage.
- Access gate relies on `request.app.state` for optional services (geoip, capture, audit) without wiring in `main.py`.
- Artifact storage returns a fake `s3://` path if `boto3` is missing, indicating a stubbed fallback (`backend/app/artifacts/storage.py`).

## Feature Parity vs. Implementation Plan
- Tasks 1-9 are partially implemented. Most backend modules exist with tests, but DB integration, geofence usage, and artifact capture are incomplete.
- Tasks 10-12 (frontend admin UI, E2E tests, Docker + README) are not implemented.

## Key Risks
- Running the app with real data is not possible without DB sessions, migrations applied, and admin data persistence.
- Access gate decisions are based on registry state that is not populated in normal API usage.
- No secure user onboarding or admin bootstrapping; all auth is in-memory and ephemeral.
