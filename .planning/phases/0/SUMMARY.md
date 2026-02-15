Phase 0 completed tasks 4-10 with commits for each task.

Work completed:
- Alembic now reads database URL from app settings.
- Added PostGIS extension migration.
- Added runtime dependencies for boto3 and psycopg[binary].
- Initialized artifact storage via settings on app startup.
- Expanded docker compose with PostGIS and MinIO services and env wiring.
- Added .env.example with local DB/S3 defaults.
- Aligned User and AccessAudit models + initial migration with missing fields.

Verification:
- Task 11 completed.
- Alembic is installed (pip show reported alembic 1.18.4).
- `alembic upgrade head` ran with env `JWT_SECRET` and `DATABASE_URL` set for local port 5433; `alembic current` shows `0002_enable_postgis (head)`.
- Docker compose stack is up via `docker compose -f infra/docker-compose.yml up -d`.
- Port adjustments in `infra/docker-compose.yml` to avoid conflicts: Postgres host 5433->5432, API host 8001->8000, MinIO host 9002->9000 and 9003->9001.
