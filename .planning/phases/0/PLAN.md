# Phase 0 Task Plan

Goal: Stand up production-like persistence and storage for backend services (DB session wiring, Postgres/PostGIS migrations, S3/MinIO config, and Docker Compose).

Notes:
- Follow existing FastAPI + SQLAlchemy 2.x patterns from repo research.
- Ensure PostGIS extension is enabled in the DB image or init.
- Prefer environment-driven configuration via settings.

## Task 1: Audit current settings and missing DB config
- Files: `backend/app/settings.py`
- Action: Confirm if database URL setting exists; if missing, define it with clear env var name and defaults for local compose.
- Output: Settings class includes DB URL and any needed Postgres-related options.

## Task 2: Add SQLAlchemy engine/session wiring
- Files: Create `backend/app/db/session.py` (or existing db module if present)
- Action: Implement engine creation + sessionmaker and FastAPI dependency `get_db()` with proper close/rollback handling.
- Output: Runtime DB sessions are available to routers/services via dependency injection.

## Task 3: Integrate session dependency into app lifecycle
- Files: `backend/app/main.py` or `backend/app/deps.py` (where dependencies are centralized)
- Action: Export `get_db()` and ensure it is imported by routers/services; update any example routers to use `Depends(get_db)` if present.
- Output: Request-scoped DB sessions are wired and ready for use.

## Task 4: Ensure Alembic migration configuration uses settings
- Files: `backend/migrations/env.py`, `backend/alembic.ini`
- Action: Inject DB URL from settings/env into Alembic config.
- Output: `alembic upgrade head` runs with configured DB URL.

## Task 5: Make PostGIS enablement explicit
- Files: Create new Alembic migration in `backend/migrations/versions/`
- Action: Add a migration that runs `CREATE EXTENSION IF NOT EXISTS postgis` (and optional `CREATE EXTENSION IF NOT EXISTS postgis_topology` if required by current models).
- Output: PostGIS extension is enabled via migrations on startup.

## Task 6: Add/verify boto3 dependency for S3 storage
- Files: `backend/pyproject.toml`
- Action: Add boto3 dependency (if missing) to ensure S3 helper works in runtime.
- Output: Storage integration can authenticate with S3/MinIO.

## Task 7: Wire S3 settings into storage initialization
- Files: `backend/app/artifacts/storage.py` or new `backend/app/artifacts/storage_factory.py`
- Action: Create a settings-backed storage instance and use it in artifact services.
- Output: Storage client configured via environment variables.

## Task 8: Update Docker Compose for Postgres/PostGIS + MinIO
- Files: `infra/docker-compose.yml`
- Action: Add `postgres` (PostGIS-enabled image) and `minio` services, volumes, ports; set API container env vars for DB + S3.
- Output: `docker compose up` starts API + PostGIS + MinIO locally.

## Task 9: Document/confirm local env defaults
- Files: `.env.example` or README if present (or add if missing)
- Action: Provide example values for DB URL, S3 endpoint, credentials, and SSL settings.
- Output: Clear guidance for local setup.

## Task 10: Audit APIs vs models/migrations and add missing fields/tables
- Files: `backend/app/api/**`, `backend/app/models/**`, `backend/migrations/versions/**`
- Action: Compare current API request/response schemas and DB usage against models and migrations; add any missing models/fields and generate migrations.
- Output: Models/migrations cover all fields required by current APIs.

## Task 11: Sanity check migrations and startup
- Commands: `alembic upgrade head`, `docker compose up`
- Action: Run migrations against local PostGIS; start services to confirm connectivity.
- Output: 
  - `alembic upgrade head` completes with no errors and logs include `Running upgrade` for the new PostGIS extension migration.
  - `docker compose up` shows healthy API, Postgres/PostGIS, and MinIO containers with no connection errors.
