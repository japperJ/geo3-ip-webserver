"""Site user repository for DB-backed persistence."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.site_user import SiteUser


def _coerce_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class SiteUserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, site_id: str, payload: Any) -> SiteUser:
        entry = SiteUser(
            site_id=_coerce_uuid(site_id),
            user_id=_coerce_uuid(payload.user_id),
            role=payload.role,
        )
        self._db.add(entry)
        self._db.flush()
        return entry

    def list_for_site(self, site_id: str) -> list[SiteUser]:
        return list(self._db.query(SiteUser).filter(SiteUser.site_id == _coerce_uuid(site_id)).all())

    def delete(self, site_id: str, user_id: str) -> None:
        entry = (
            self._db.query(SiteUser)
            .filter(SiteUser.site_id == _coerce_uuid(site_id))
            .filter(SiteUser.user_id == _coerce_uuid(user_id))
            .first()
        )
        if entry is not None:
            self._db.delete(entry)
