from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.admin_deps import require_admin
from app.db.session import get_db
from app.admin.repositories.geofence_repository import GeofenceRepository
from app.admin.repositories.serialization import geofence_to_dict
from app.admin.repositories.site_repository import SiteRepository

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
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> dict:
    site_repo = SiteRepository(db)
    if site_repo.get(site_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    repo = GeofenceRepository(db)
    geofence = repo.create(site_id, payload)
    response = geofence_to_dict(geofence)
    response["polygon"] = payload.polygon
    response["center"] = payload.center
    response["radius"] = payload.radius_meters
    return response


@router.get("")
def list_geofences(
    site_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> list[dict]:
    site_repo = SiteRepository(db)
    if site_repo.get(site_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    repo = GeofenceRepository(db)
    return repo.list_for_site(site_id)
