"""IP rule repository for DB-backed persistence."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.ip_rule import IPRule


def _coerce_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class IPRuleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, site_id: str, payload: Any) -> IPRule:
        rule = IPRule(
            site_id=_coerce_uuid(site_id),
            cidr=payload.cidr,
            action=payload.action,
        )
        self._db.add(rule)
        self._db.flush()
        return rule

    def list_for_site(self, site_id: str) -> list[IPRule]:
        return list(self._db.query(IPRule).filter(IPRule.site_id == _coerce_uuid(site_id)).all())
