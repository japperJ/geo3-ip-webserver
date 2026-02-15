from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.admin_deps import require_admin
from app.db.models.site import SiteFilterMode
from app.db.session import get_db
from app.admin.repositories.serialization import site_to_dict
from app.admin.repositories.site_repository import SiteRepository

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
    repo = SiteRepository(db)
    try:
        site = repo.create(payload)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hostname already exists")
    return site_to_dict(site)


@router.get("")
def list_sites(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> list[dict]:
    repo = SiteRepository(db)
    return [site_to_dict(site) for site in repo.list_all()]


@router.patch("/{site_id}")
def update_site(
    site_id: str,
    payload: SiteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> dict:
    repo = SiteRepository(db)
    site = repo.get(site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    try:
        site = repo.update(site, payload)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hostname already exists")
    return site_to_dict(site)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(
    site_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> Response:
    repo = SiteRepository(db)
    site = repo.get(site_id)
    if site is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    repo.delete(site)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
