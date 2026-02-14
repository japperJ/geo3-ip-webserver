# Phase 0 Research: Foundation (Persistence + Infra)

## Summary
Phase 0 requires wiring runtime persistence (SQLAlchemy session/engine), enabling Postgres/PostGIS migrations, and configuring S3-compatible storage plus Docker Compose. The codebase already has SQLAlchemy models, Alembic migration scaffolding, and an S3-compatible storage helper, but lacks runtime DB session wiring and any Postgres/MinIO services in Compose. Research below focuses on how to implement these items using existing code patterns and where gaps remain.

## Standard Stack
| Need | Solution | Version | Confidence | Source |
|---|---|---|---|---|
| Web API | FastAPI | >=0.110.0 | HIGH | `backend/pyproject.toml` |
| ORM | SQLAlchemy | >=2.0.25 | HIGH | `backend/pyproject.toml` |
| Migrations | Alembic | >=1.13.0 | HIGH | `backend/pyproject.toml`, `backend/migrations/env.py` |
| PostGIS types | GeoAlchemy2 | >=0.15.2 | HIGH | `backend/pyproject.toml`, `backend/migrations/versions/0001_core_tables.py` |
| S3 client | boto3 | (not declared) | MEDIUM | `backend/app/artifacts/storage.py` |
| Settings | pydantic-settings | >=2.2.1 | HIGH | `backend/pyproject.toml`, `backend/app/settings.py` |

## Architecture Patterns
### Pattern: SQLAlchemy 2.x Session Factory + FastAPI Dependency
Use a single Engine with `sessionmaker` or `async_sessionmaker` and expose DB sessions via FastAPI dependencies in request scope. The repo already defines models and Alembic metadata but lacks engine/session wiring. Plan should add a `db/session.py` (or similar) with:
- `DATABASE_URL` from settings
- engine creation
- session factory
- dependency `get_db()` to yield and close session

### Pattern: Alembic-driven schema for PostGIS
`backend/migrations/versions/0001_core_tables.py` uses PostGIS types (`Geometry`, `INET`, `JSONB`) and GIST indexes. Postgres must have the PostGIS extension enabled in migrations or pre-provisioned in the database image/entrypoint. Alembic env is standard `engine_from_config` and reads `sqlalchemy.url` from `alembic.ini` or config overrides.

### Pattern: S3-compatible storage configured from Settings
`S3CompatibleStorage` accepts bucket, endpoint URL, region, access key, secret key, and `use_ssl`. These are already present in `backend/app/settings.py`. Plan should wire settings into storage initialization in artifact-related services and ensure required env vars exist.

### Pattern: Docker Compose for Local Infra
Existing `infra/docker-compose.yml` runs only the API container. Phase 0 needs to add Postgres/PostGIS and MinIO services plus environment variables for the API container to point at them. Compose should include volumes for persistence and expose ports for local tooling (Postgres 5432, MinIO 9000/9001).

## Don't Hand-Roll
| Feature | Use Instead | Why |
|---|---|---|
| S3 protocol | boto3 S3 client | Already used by storage helper; avoids custom HTTP signing. |
| DB migrations | Alembic | Existing configuration and migration scripts rely on Alembic. |
| PostGIS geometry types | GeoAlchemy2 | Already used in models/migrations; avoids custom WKT parsing. |

## Common Pitfalls
1. **PostGIS extension not enabled** — Geometry columns require PostGIS; ensure extension is installed/enabled in DB image or migration bootstrap. Mitigation: use a PostGIS-enabled image in Compose and/or run `CREATE EXTENSION postgis` at init.
2. **Alembic URL mismatch** — `alembic.ini` has no URL. Migrations will fail if `sqlalchemy.url` is not provided via env or config override. Mitigation: set env var and pass to Alembic config during migration commands.
3. **Session lifecycle leaks** — Without proper dependency scoping, sessions can leak or fail to commit/rollback. Mitigation: `try/except/finally` in dependency, rollback on exceptions.
4. **Missing boto3 dependency** — `backend/app/artifacts/storage.py` imports boto3 dynamically; if not installed, it returns a stubbed `s3://` path. Mitigation: add boto3 to dependencies and ensure credentials are set.
5. **MinIO endpoint URL and SSL mismatch** — `artifact_use_ssl` defaults to true; MinIO local typically uses HTTP. Mitigation: set `artifact_use_ssl=false` in local env and `artifact_endpoint_url` to http://minio:9000.

## Code Examples
Verified patterns in repo (to be implemented, not present yet):

```python
# app/db/session.py (proposed)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# app/artifacts/storage_factory.py (proposed)
from app.artifacts.storage import S3CompatibleStorage
from app.settings import settings

storage = S3CompatibleStorage(
    bucket=settings.artifact_bucket,
    endpoint_url=settings.artifact_endpoint_url,
    region_name=settings.artifact_region,
    access_key=settings.artifact_access_key,
    secret_key=settings.artifact_secret_key,
    use_ssl=settings.artifact_use_ssl,
)
```

## Open Questions
1. What is the intended name and location of the DB URL setting (not present in `backend/app/settings.py`)?
2. Should migrations run via Alembic CLI in container startup or via a separate job/command in Compose?
3. Is there a preferred PostGIS Docker image (e.g., `postgis/postgis` vs custom), and should it handle extension creation?
4. Should MinIO credentials be static in Compose or loaded via `.env`?

## Sources
| Source | Type | Confidence |
|---|---|---|
| `backend/pyproject.toml` | codebase | HIGH |
| `backend/migrations/env.py` | codebase | HIGH |
| `backend/migrations/versions/0001_core_tables.py` | codebase | HIGH |
| `backend/app/settings.py` | codebase | HIGH |
| `backend/app/artifacts/storage.py` | codebase | HIGH |
| `infra/docker-compose.yml` | codebase | HIGH |
