from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.admin_store import get_admin_store
from app.auth.admin_deps import require_admin

router = APIRouter(prefix="/api/admin/sites/{site_id}/geofences", tags=["admin-geofences"])


class GeofenceCreate(BaseModel):
    name: str | None = None
    polygon: list[list[float]] | None = None
    center: list[float] | None = None
    radius_meters: int | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_geofence(
    site_id: str,
    payload: GeofenceCreate,
    request: Request,
    user=Depends(require_admin),
) -> dict:
    store = get_admin_store(request.app)
    if site_id not in store.sites:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    geofence = {
        "id": store.new_id(),
        "site_id": site_id,
        "name": payload.name,
        "polygon": payload.polygon,
        "center": payload.center,
        "radius_meters": payload.radius_meters,
    }
    store.geofences.setdefault(site_id, []).append(geofence)
    return geofence


@router.get("")
def list_geofences(site_id: str, request: Request, user=Depends(require_admin)) -> list[dict]:
    store = get_admin_store(request.app)
    if site_id not in store.sites:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return list(store.geofences.get(site_id, []))
