from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.admin_store import get_admin_store
from app.auth.admin_deps import require_admin
from app.db.models.site import SiteFilterMode
from app.db.session import get_db

router = APIRouter(prefix="/api/admin/sites", tags=["admin-sites"])


class SiteCreate(BaseModel):
    name: str
    hostname: str | None = None
    owner_user_id: str
    filter_mode: SiteFilterMode | None = None


class SiteUpdate(BaseModel):
    name: str | None = None
    hostname: str | None = None
    filter_mode: SiteFilterMode | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_site(
    payload: SiteCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> dict:
    store = get_admin_store(request.app)
    site_id = store.new_id()
    site = {
        "id": site_id,
        "name": payload.name,
        "hostname": payload.hostname,
        "owner_user_id": payload.owner_user_id,
        "filter_mode": (payload.filter_mode or SiteFilterMode.DISABLED).value,
    }
    store.sites[site_id] = site
    return site


@router.get("")
def list_sites(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> list[dict]:
    store = get_admin_store(request.app)
    return list(store.sites.values())


@router.patch("/{site_id}")
def update_site(
    site_id: str,
    payload: SiteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> dict:
    store = get_admin_store(request.app)
    site = store.sites.get(site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if payload.name is not None:
        site["name"] = payload.name
    if payload.hostname is not None:
        site["hostname"] = payload.hostname
    if payload.filter_mode is not None:
        site["filter_mode"] = payload.filter_mode.value
    return site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(
    site_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> Response:
    store = get_admin_store(request.app)
    store.sites.pop(site_id, None)
    store.geofences.pop(site_id, None)
    store.ip_rules.pop(site_id, None)
    store.site_users.pop(site_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
