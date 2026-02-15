"""Serialization helpers for admin repositories."""

from __future__ import annotations

from typing import Any


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
