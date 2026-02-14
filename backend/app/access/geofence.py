from __future__ import annotations

import math
from typing import Iterable


def within_geofence(
    *,
    point: tuple[float, float],
    polygon: Iterable[tuple[float, float]] | None,
    center: tuple[float, float] | None,
    radius_meters: float | None,
) -> bool:
    if polygon:
        return _point_in_polygon(point, list(polygon))
    if center and radius_meters is not None:
        return _haversine_meters(point, center) <= radius_meters
    return False


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    n = len(polygon)
    if n >= 2 and polygon[0] == polygon[-1]:
        polygon = polygon[:-1]
        n -= 1
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        dx = xj - xi
        dy = yj - yi
        cross = (x - xi) * dy - (y - yi) * dx
        if cross == 0.0:
            if min(xi, xj) <= x <= max(xi, xj) and min(yi, yj) <= y <= max(yi, yj):
                return True
        intersects = (yi > y) != (yj > y)
        if intersects:
            x_at_y = (xj - xi) * (y - yi) / (yj - yi + 0.0) + xi
            if x < x_at_y:
                inside = not inside
        j = i
    return inside


def _haversine_meters(point: tuple[float, float], center: tuple[float, float]) -> float:
    lon1, lat1 = point
    lon2, lat2 = center
    r = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
        dlambda / 2
    ) ** 2
    return 2 * r * math.asin(math.sqrt(a))
