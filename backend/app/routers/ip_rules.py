from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.admin_deps import require_admin
from app.db.session import get_db
from app.db.models.ip_rule import IPRuleAction
from app.admin.repositories.ip_rule_repository import IPRuleRepository
from app.admin.repositories.serialization import ip_rule_to_dict
from app.admin.repositories.site_repository import SiteRepository

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
    site_repo = SiteRepository(db)
    if site_repo.get(site_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    repo = IPRuleRepository(db)
    rule = repo.create(site_id, payload)
    return ip_rule_to_dict(rule)


@router.get("")
def list_ip_rules(
    site_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
) -> list[dict]:
    site_repo = SiteRepository(db)
    if site_repo.get(site_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    repo = IPRuleRepository(db)
    return [ip_rule_to_dict(rule) for rule in repo.list_for_site(site_id)]
