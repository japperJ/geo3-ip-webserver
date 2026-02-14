import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IPRuleAction(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"


class IPRule(Base):
    __tablename__ = "ip_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False
    )
    cidr: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[IPRuleAction] = mapped_column(
        Enum(IPRuleAction, name="ip_rule_action", native_enum=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    site: Mapped["Site"] = relationship(back_populates="ip_rules")
