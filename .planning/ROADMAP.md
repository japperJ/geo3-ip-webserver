# Roadmap

## Phase 0: Foundation (Persistence + Infra)
**Goal:** Stand up production-like persistence and storage for backend services.
- Add DB session/engine wiring and configuration for Postgres/PostGIS.
- Ensure migrations run cleanly; add missing models/fields needed by current APIs.
- Add S3/MinIO configuration and credentials management.
- Provide Docker Compose for API + Postgres/PostGIS + MinIO.

## Phase 1: Persisted Admin APIs
**Goal:** Replace in-memory admin stores with SQLAlchemy-backed repositories.
- Implement repository layer and CRUD for sites, geofences, IP rules, and site users.
- Update admin routers to use DB-backed stores.
- Add cache invalidation or refresh for site config registry.
- Update tests to use DB fixtures.

## Phase 2: Access Gate Integration
**Goal:** Ensure access decisions reflect persisted site configs and geofences.
- Populate and keep in sync the access-gate registry from DB data.
- Use geofence containment checks (PostGIS where possible).
- Handle GeoIP lookups using DB-backed cache overrides where relevant.

## Phase 3: Auditing + Artifacts
**Goal:** Persist audit logs and artifact metadata; store payloads in S3/MinIO.
- Wire audit service to `AccessAudit` model with DB persistence.
- Add artifact metadata persistence and storage integration.
- Implement or stub capture service with clear TODOs and config flags.

## Phase 4: Operational Hardening
**Goal:** Make local/dev setup reliable and document operational workflows.
- Add README with local setup, migrations, and env config.
- Add health checks, seed/bootstrapping scripts, and admin bootstrap flow.
- Add basic observability (structured logging, error reporting hooks).
