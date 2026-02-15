"""IP rule repository for DB-backed persistence."""

from __future__ import annotations

from sqlalchemy.orm import Session


class IPRuleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db
