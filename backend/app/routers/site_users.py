from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.admin_store import get_admin_store
from app.auth.admin_deps import require_admin
from app.db.models.site_user import SiteUserRole

router = APIRouter(prefix="/api/admin/sites/{site_id}/users", tags=["admin-site-users"])


class SiteUserCreate(BaseModel):
    user_id: str
    role: SiteUserRole


@router.post("", status_code=status.HTTP_201_CREATED)
def add_site_user(
    site_id: str,
    payload: SiteUserCreate,
    request: Request,
    user=Depends(require_admin),
) -> dict:
    store = get_admin_store(request.app)
    if site_id not in store.sites:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    entry = {
        "id": store.new_id(),
        "site_id": site_id,
        "user_id": payload.user_id,
        "role": payload.role.value,
    }
    site_users = store.site_users.setdefault(site_id, {})
    site_users[payload.user_id] = entry
    return entry


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_site_user(
    site_id: str,
    user_id: str,
    request: Request,
    user=Depends(require_admin),
) -> Response:
    store = get_admin_store(request.app)
    site_users = store.site_users.get(site_id)
    if site_users is not None:
        site_users.pop(user_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
