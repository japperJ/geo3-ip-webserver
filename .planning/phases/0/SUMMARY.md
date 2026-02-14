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
- Task 11 attempted.
- `alembic upgrade head` failed because alembic is not installed in the environment.
- `docker compose -f infra/docker-compose.yml up -d` failed because port 5432 was already allocated.
- Brought compose stack down after the failed start.
