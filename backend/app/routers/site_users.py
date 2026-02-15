from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.admin_deps import require_admin
from app.db.models.site_user import SiteUserRole
from app.db.session import get_db
from app.admin.repositories.site_repository import SiteRepository
from app.admin.repositories.site_user_repository import SiteUserRepository
from app.admin.repositories.serialization import site_user_to_dict

router = APIRouter(prefix="/api/admin/sites/{site_id}/users", tags=["admin-site-users"])


class SiteUserCreate(BaseModel):
    user_id: str
    role: SiteUserRole


@router.post("", status_code=status.HTTP_201_CREATED)
def add_site_user(
    site_id: str,
    payload: SiteUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> dict:
    site_repo = SiteRepository(db)
    if site_repo.get(site_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    repo = SiteUserRepository(db)
    try:
        entry = repo.create(site_id, payload)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    return site_user_to_dict(entry)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_site_user(
    site_id: str,
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> Response:
    repo = SiteUserRepository(db)
    repo.delete(site_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
