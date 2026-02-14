# Requirements

## Product Goal
Deliver an MVP backend-first system with production-like persistence using Postgres/PostGIS and S3-compatible object storage (MinIO in local/dev), enabling persisted admin configuration, access decisions, auditing, and artifact storage.

## Functional Requirements
- Persist sites, geofences, IP rules, and site users in Postgres.
- Evaluate access decisions using persisted site config, IP rules, and geofence containment.
- Provide GeoIP lookup with caching and optional DB-backed overrides.
- Persist access audit logs and support export (CSV or API pagination).
- Store artifact metadata in Postgres and artifact payloads in S3/MinIO.
- Provide admin APIs for CRUD on sites, geofences, IP rules, and site users using database persistence.
- Provide auth using persisted users, with secure password hashing and JWT issuance.

## Non-Functional Requirements
- Use Postgres with PostGIS enabled; run migrations for schema setup.
- Support local/dev with Docker Compose for API + Postgres/PostGIS + MinIO.
- Keep API behavior stable for existing tests or update tests to match persistence.
- Keep access-gate latency low by caching site configs; ensure cache invalidation on updates.

## MVP Scope Boundaries
- Frontend remains out of scope for MVP; API-only backend readiness.
- Playwright capture implementation can be stubbed if artifact metadata and storage are wired.
- RBAC can be minimal (admin vs site user) as long as persistence is real.
