# Phase 5 Research: IP geolocation with cache

## Summary
Researched MaxMind GeoIP2 Python usage (database reader + web service), MaxMind DB reader behaviors, and caching options. Recommended: use `geoip2` for database lookups, reuse a long-lived `geoip2.database.Reader`, and add a two-tier cache (in-memory TTL/LRU + persistent DB cache keyed by IP and database version). Avoid caching by localized `names` fields and be explicit about cache invalidation when the MMDB file updates. Codesearch was not available in this environment, so findings rely on official docs and package repositories.

## Standard Stack
| Need | Solution | Version | Confidence | Source |
|---|---|---|---|---|
| GeoIP2 database/web service API | `geoip2` | 5.2.0 | HIGH | https://pypi.org/project/geoip2/ ; https://github.com/maxmind/GeoIP2-python |
| MaxMind DB reader (optional direct usage) | `maxminddb` | 3.0.0 | HIGH | https://github.com/maxmind/MaxMind-DB-Reader-python |
| In-memory TTL/LRU cache | `cachetools` | 7.0.1 | MEDIUM | https://pypi.org/project/cachetools/ |
| Dogpile lock + pluggable cache backends | `dogpile.cache` | 1.5.0 | MEDIUM | http://dogpilecache.sqlalchemy.org/en/latest/ |
| MaxMind database docs | MaxMind Developer Portal | N/A | HIGH | https://dev.maxmind.com/geoip/docs/databases/ |

## Architecture Patterns
### Pattern: Long-lived Reader + two-tier cache
Use a long-lived `geoip2.database.Reader` instance (creation is expensive) for MMDB lookups. Front it with an in-memory TTL/LRU cache for hot IPs. Persist misses or selected results into a DB cache table to share across processes and survive restarts. Key the DB cache by `ip` plus `db_version` (or database build epoch) so cache entries are invalidated on database updates.

Key points:
- Reader creation is expensive; reuse across requests. (GeoIP2 Python README)
- Database lookups can return partial data; always handle missing attributes. (GeoIP2 Python README)
- Cache invalidation must be tied to MMDB updates; MaxMind updates databases regularly. (MaxMind docs)

### Pattern: IP normalization and keying
Normalize input IPs (string form) before caching. Consider caching by network prefix returned by the reader (when available) to maximize hit rate for adjacent IPs. For DB persistence, store both original IP and resolved network/prefix when available.

## Don't Hand-Roll
| Feature | Use Instead | Why |
|---|---|---|
| GeoIP2 parsing | `geoip2` | Official client for databases and web service; handles model structure and errors. |
| MMDB binary parsing | `maxminddb` or `geoip2` | Format is non-trivial; official reader provides safe access. |
| Cache stampede control | `dogpile.cache` | Provides dogpile locking to avoid thundering herd. |

## Common Pitfalls
1. **Recreating Reader per request** — Reader creation is expensive; reuse a singleton per process. (GeoIP2 Python README)
2. **Caching by localized `names` fields** — MaxMind warns that `names` values can change; use stable ids (geoname_id, iso_code). (GeoIP2 Python README)
3. **Forgetting database update invalidation** — MMDB updates invalidate prior cache entries; include db version in keys or expire aggressively. (MaxMind docs)
4. **Ignoring AddressNotFoundError** — Missing IPs raise `AddressNotFoundError`; decide whether to cache negative results with shorter TTL. (GeoIP2 Python README)
5. **Concurrent close on readers** — MaxMind DB reader warns closing while reads in progress can raise exceptions; avoid closing while serving traffic. (MaxMind DB reader README)
6. **Multi-process in-memory cache** — LRU/TTL in-memory caches are per-process; use DB cache for shared results. (General architecture)

## Code Examples
Verified minimal usage patterns from GeoIP2 Python README:

```python
import geoip2.database

# Reuse the same Reader across requests
with geoip2.database.Reader("/path/to/GeoLite2-City.mmdb") as reader:
    response = reader.city("203.0.113.0")
    country = response.country.iso_code
```

In-memory TTL/LRU cache usage (from cachetools examples):

```python
from cachetools import TTLCache

cache = TTLCache(maxsize=1024, ttl=600)
```

## Open Questions
- What DB is available for the persistent cache (Postgres, SQLite, Redis, etc.)?
- Desired cache TTLs and acceptable staleness window after MMDB updates.
- Whether to use MaxMind web service as fallback if MMDB lacks data.

## Sources
| Source | Type | Confidence |
|---|---|---|
| https://github.com/maxmind/GeoIP2-python | Official | HIGH |
| https://pypi.org/project/geoip2/ | Official | HIGH |
| https://github.com/maxmind/MaxMind-DB-Reader-python | Official | HIGH |
| https://dev.maxmind.com/geoip/docs/databases/ | Official | HIGH |
| https://pypi.org/project/cachetools/ | Official | MEDIUM |
| http://dogpilecache.sqlalchemy.org/en/latest/ | Official | MEDIUM |
