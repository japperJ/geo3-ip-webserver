"""Geofence repository for DB-backed persistence."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from geoalchemy2.functions import ST_AsGeoJSON
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.admin.repositories.serialization import json_to_list, point_to_wkt, polygon_to_wkt
from app.db.models.geofence import Geofence


def _coerce_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class GeofenceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, site_id: str, payload: Any) -> Geofence:
        geofence = Geofence(
            site_id=_coerce_uuid(site_id),
            name=payload.name,
            polygon=polygon_to_wkt(payload.polygon),
            center=point_to_wkt(payload.center),
            radius_meters=payload.radius_meters,
        )
        self._db.add(geofence)
        self._db.flush()
        return geofence

    def list_for_site(self, site_id: str) -> list[dict[str, Any]]:
        rows = (
            self._db.query(
                Geofence,
                func.ST_AsGeoJSON(Geofence.polygon).label("polygon_json"),
                func.ST_AsGeoJSON(Geofence.center).label("center_json"),
            )
            .filter(Geofence.site_id == _coerce_uuid(site_id))
            .all()
        )
        results: list[dict[str, Any]] = []
        for geofence, polygon_json, center_json in rows:
            results.append(
                {
                    "id": geofence.id,
                    "site_id": geofence.site_id,
                    "name": geofence.name,
                    "polygon": json_to_list(polygon_json),
                    "center": json_to_list(center_json),
                    "radius": geofence.radius_meters,
                }
            )
        return results
