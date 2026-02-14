# Current State

## Snapshot
- Backend core logic and admin APIs exist but are wired to in-memory stores.
- SQLAlchemy models and migrations exist but there is no runtime DB session wiring.
- Access gate uses a registry that is never populated from persisted data.
- GeoIP cache and geofence logic exist but are not enforced in access decisions.
- Audit logging and artifact handling are in-memory or stubbed.
- Docker setup runs only the API container; no Postgres/PostGIS or S3/MinIO.
- Frontend is a placeholder.

## MVP Readiness Gaps (Backend-First)
- Postgres/PostGIS and S3-compatible storage are not configured or integrated.
- Admin APIs do not persist to the database.
- Access gate is not using stored site configs or geofence containment.
- Audit logs are not persisted.
- Artifact metadata is not stored; capture service is not implemented.

## Immediate Risks
- Production-like persistence is not possible without DB session management.
- Access decisions are not reliable because site configs are not synchronized.
- Audit trails are ephemeral.
