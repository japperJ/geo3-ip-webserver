import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AccessDecision(str, enum.Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


class AccessAudit(Base):
    __tablename__ = "access_audit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    client_ip: Mapped[str | None] = mapped_column(String(50))
    ip_geo_lat: Mapped[float | None] = mapped_column(nullable=True)
    ip_geo_lng: Mapped[float | None] = mapped_column(nullable=True)
    ip_geo_country: Mapped[str | None] = mapped_column(String(10))
    client_gps: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326))
    decision: Mapped[AccessDecision | None] = mapped_column(
        Enum(AccessDecision, name="access_decision", native_enum=False)
    )
    reason: Mapped[str | None] = mapped_column(Text)
    artifact_path: Mapped[str | None] = mapped_column(String(500))

    site: Mapped["Site"] = relationship(back_populates="audits")
