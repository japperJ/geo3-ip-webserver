"""Serialization helpers for admin repositories."""

from __future__ import annotations

import json
from typing import Any, cast

from geoalchemy2.elements import WKTElement


def site_to_dict(site: Any) -> dict[str, Any]:
    return {
        "id": str(site.id),
        "name": site.name,
        "hostname": site.hostname,
        "owner_user_id": str(site.owner_user_id),
        "filter_mode": getattr(site.filter_mode, "value", site.filter_mode),
    }


def geofence_to_dict(geofence: Any) -> dict[str, Any]:
    return {
        "id": str(geofence.id),
        "site_id": str(geofence.site_id),
        "name": geofence.name,
        "polygon": geofence.polygon,
        "center": geofence.center,
        "radius": geofence.radius,
    }


def polygon_to_wkt(polygon: list[list[float]] | None) -> WKTElement | None:
    if not polygon:
        return None
    if polygon[0] != polygon[-1]:
        polygon = [*polygon, polygon[0]]
    points = ", ".join(f"{lng} {lat}" for lng, lat in polygon)
    return WKTElement(f"POLYGON(({points}))", srid=4326)


def point_to_wkt(point: list[float] | None) -> WKTElement | None:
    if not point:
        return None
    return WKTElement(f"POINT({point[0]} {point[1]})", srid=4326)


def json_to_list(value: str | None) -> list[list[float]] | list[float] | None:
    if not value:
        return None
    data = json.loads(value)
    if isinstance(data, dict) and "coordinates" in data:
        coords = data["coordinates"]
        if isinstance(coords, list):
            return cast(list[list[float]] | list[float], coords)
        return None
    if isinstance(data, list):
        return cast(list[list[float]] | list[float], data)
    return None


def ip_rule_to_dict(rule: Any) -> dict[str, Any]:
    return {
        "id": str(rule.id),
        "site_id": str(rule.site_id),
        "cidr": rule.cidr,
        "action": getattr(rule.action, "value", rule.action),
    }


def site_user_to_dict(site_user: Any) -> dict[str, Any]:
    return {
        "id": str(site_user.id),
        "site_id": str(site_user.site_id),
        "user_id": str(site_user.user_id),
        "role": getattr(site_user.role, "value", site_user.role),
    }
