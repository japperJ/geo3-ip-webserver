"""Site repository for DB-backed persistence."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.site import Site, SiteFilterMode
from app.db.models.user import User


def _coerce_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class SiteRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, payload: Any) -> Site:
        owner_id = _coerce_uuid(payload.owner_user_id)
        existing_owner = self._db.get(User, owner_id)
        if existing_owner is None:
            self._db.add(User(id=owner_id, email=f"owner-{owner_id}@local"))
        site = Site(
            name=payload.name,
            hostname=payload.hostname,
            owner_user_id=owner_id,
            filter_mode=payload.filter_mode or SiteFilterMode.DISABLED,
        )
        self._db.add(site)
        self._db.flush()
        return site

    def list_all(self) -> list[Site]:
        return list(self._db.query(Site).all())

    def get(self, site_id: str) -> Site | None:
        return self._db.get(Site, _coerce_uuid(site_id))

    def update(self, site: Site, payload: Any) -> Site:
        if payload.name is not None:
            site.name = payload.name
        if payload.hostname is not None:
            site.hostname = payload.hostname
        if payload.filter_mode is not None:
            site.filter_mode = payload.filter_mode
        self._db.flush()
        return site

    def delete(self, site: Site) -> None:
        self._db.delete(site)
