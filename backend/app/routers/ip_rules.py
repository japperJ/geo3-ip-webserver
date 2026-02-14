from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.admin_store import get_admin_store
from app.auth.admin_deps import require_admin
from app.db.session import get_db
from app.db.models.ip_rule import IPRuleAction

router = APIRouter(prefix="/api/admin/sites/{site_id}/ip-rules", tags=["admin-ip-rules"])


class IPRuleCreate(BaseModel):
    cidr: str
    action: IPRuleAction


@router.post("", status_code=status.HTTP_201_CREATED)
def create_ip_rule(
    site_id: str,
    payload: IPRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> dict:
    store = get_admin_store(request.app)
    if site_id not in store.sites:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    rule = {
        "id": store.new_id(),
        "site_id": site_id,
        "cidr": payload.cidr,
        "action": payload.action.value,
    }
    store.ip_rules.setdefault(site_id, []).append(rule)
    return rule


@router.get("")
def list_ip_rules(
    site_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> list[dict]:
    store = get_admin_store(request.app)
    if site_id not in store.sites:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return list(store.ip_rules.get(site_id, []))
