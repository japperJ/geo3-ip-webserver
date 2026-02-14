from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4



@dataclass
class AdminStore:
    sites: dict[str, dict[str, Any]] = field(default_factory=dict)
    geofences: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    ip_rules: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    site_users: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)

    def new_id(self) -> str:
        return str(uuid4())

    def clear(self) -> None:
        self.sites.clear()
        self.geofences.clear()
        self.ip_rules.clear()
        self.site_users.clear()


def get_admin_store(app) -> AdminStore:
    store = getattr(app.state, "admin_store", None)
    if store is None:
        store = AdminStore()
        app.state.admin_store = store
    return store


def clear_admin_store(app) -> None:
    store = getattr(app.state, "admin_store", None)
    if store is not None:
        store.clear()
