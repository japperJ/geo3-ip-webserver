# Phase 1 Research: Persisted Admin APIs

## Summary
Phase 1 replaces the in-memory admin store (`app/admin_store.py`) with SQLAlchemy-backed repositories for sites, geofences, IP rules, and site users, then rewires admin routers to use the DB. The codebase already has models, migrations, and a DB session dependency; the current admin routers still ignore the DB session and mutate in-memory dictionaries. Research below focuses on repository patterns that fit the existing SQLAlchemy 2.x usage, how to map API payloads to models (including PostGIS geometry), and how to keep the access-gate site registry refreshed after admin writes.

## Standard Stack
| Need | Solution | Version | Confidence | Source |
|---|---|---|---|---|
| Web API | FastAPI | >=0.110.0 | HIGH | `backend/pyproject.toml` |
| ORM | SQLAlchemy | >=2.0.25 | HIGH | `backend/pyproject.toml`, `backend/app/db/session.py` |
| Migrations | Alembic | >=1.13.0 | HIGH | `backend/pyproject.toml`, `backend/migrations/env.py` |
| PostGIS types | GeoAlchemy2 | >=0.15.2 | HIGH | `backend/pyproject.toml`, `backend/app/db/models/geofence.py` |
| DB driver | psycopg | >=3.1.18 | HIGH | `backend/pyproject.toml` |

## Architecture Patterns
### Pattern: Repository layer over SQLAlchemy Session
Admin routers already depend on `get_db()` but ignore it. Introduce repositories that accept a `Session` and provide CRUD methods for `Site`, `Geofence`, `IPRule`, and `SiteUser`. Keep transaction boundaries in the request-scoped `get_db()` dependency (`commit` on success, `rollback` on error) so repositories stay thin.

Suggested responsibilities:
- `SiteRepository`: create/list/update/delete `Site`, enforce unique hostname, handle cascading deletes for related tables.
- `GeofenceRepository`: create/list per site; map API payloads to `Geofence` with geometry conversion.
- `IPRuleRepository`: create/list per site; ensure `IPRuleAction` enum mapping.
- `SiteUserRepository`: create/delete per site; avoid duplicates for `(site_id, user_id)`.

### Pattern: ID Types and Serialization
Models use UUID primary keys. Admin routes currently return string IDs from `uuid4()` in memory. When moving to DB, normalize by returning `str(model.id)` in API responses to keep JSON payloads stable.

### Pattern: Geometry conversion for geofences
`Geofence` stores `polygon` and `center` as GeoAlchemy2 Geometry. Admin API payloads are lists of coordinates (polygon) or `[lng, lat]` (center). Repositories should convert to WKT/GeoAlchemy2 shapes for inserts and back to lists for responses. The repo currently does not include a geometry serialization helper, so the planner should either:
- Use `geoalchemy2.shape.from_shape` and `shapely` (if added) to convert to geometry, or
- Use `GeoAlchemy2` WKT helpers with `ST_GeomFromText` in SQLAlchemy expressions.

### Pattern: Access-gate site registry refresh
`app/middleware/access_gate.py` uses an in-memory `SiteConfigRegistry` that is never populated from DB. Phase 1 includes “cache invalidation or refresh for site config registry.” The admin routers should trigger a refresh after site/geo/ip updates. Options:
- Rebuild registry entries from DB per write (simple, safe; acceptable for low volume).
- Invalidate only affected hostnames by deleting keys and lazy-reloading on next access (requires adding lazy-load path in middleware).

## Don't Hand-Roll
| Feature | Use Instead | Why |
|---|---|---|
| DB session lifecycle | `get_db()` dependency | Already handles commit/rollback/close in `backend/app/db/session.py`. |
| UUID generation | SQLAlchemy defaults | Models already default to `uuid.uuid4` for PKs. |
| Enum mapping | SQLAlchemy Enum + Pydantic | Models define `SiteFilterMode`, `IPRuleAction`, `SiteUserRole` enums. |

## Common Pitfalls
1. **Returning raw SQLAlchemy objects** — FastAPI can’t serialize ORM objects without Pydantic models. Mitigation: map to dict responses, or add response models.
2. **Geometry serialization gaps** — `Geometry` columns won’t serialize to JSON directly. Mitigation: add explicit conversion to/from list coordinates in repositories.
3. **Unique hostname conflicts** — `Site.hostname` is unique; create/update should handle integrity errors and return 409.
4. **Session commit timing** — `get_db()` commits after route returns; if repository code needs the new ID immediately, call `db.flush()` before reading `id`.
5. **Registry drift** — Access-gate registry stays stale unless admin writes trigger refresh/invalidation.

## Code Examples
Verified patterns in repo (to be implemented, not present yet):

```python
# Example repository signature (DB session already exists)
class SiteRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, payload: SiteCreate) -> Site:
        site = Site(
            name=payload.name,
            hostname=payload.hostname,
            owner_user_id=payload.owner_user_id,
            filter_mode=payload.filter_mode or SiteFilterMode.DISABLED,
        )
        self._db.add(site)
        self._db.flush()
        return site
```

```python
# Example refresh hook after admin write
def refresh_site_registry(db: Session, app: FastAPI) -> None:
    clear_site_configs(app)
    for site in db.query(Site).all():
        register_site_config(app, site.hostname, SiteAccessConfig(...))
```

## Open Questions
1. Is a new response schema expected for admin endpoints, or should responses stay as dicts matching current tests?
2. Are soft deletes required for sites or related data, or is hard delete acceptable (current behavior is hard delete)?
3. For geofences, should the API accept both polygon and circle in one payload (current model allows both), and how should conflicts be resolved?
4. What is the intended refresh strategy for `SiteConfigRegistry` (full rebuild vs targeted invalidation vs lazy load)?

## Sources
| Source | Type | Confidence |
|---|---|---|
| `backend/app/admin_store.py` | codebase | HIGH |
| `backend/app/routers/sites.py` | codebase | HIGH |
| `backend/app/routers/geofences.py` | codebase | HIGH |
| `backend/app/routers/ip_rules.py` | codebase | HIGH |
| `backend/app/routers/site_users.py` | codebase | HIGH |
| `backend/app/db/session.py` | codebase | HIGH |
| `backend/app/db/models/site.py` | codebase | HIGH |
| `backend/app/db/models/geofence.py` | codebase | HIGH |
| `backend/app/db/models/ip_rule.py` | codebase | HIGH |
| `backend/app/db/models/site_user.py` | codebase | HIGH |
| `backend/app/middleware/access_gate.py` | codebase | HIGH |
