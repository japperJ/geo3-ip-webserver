import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SiteFilterMode(str, enum.Enum):
    DISABLED = "disabled"
    IP = "ip"
    GEO = "geo"
    IP_AND_GEO = "ip_and_geo"


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255), index=True, unique=True)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    filter_mode: Mapped[SiteFilterMode] = mapped_column(
        Enum(SiteFilterMode, name="site_filter_mode", native_enum=False),
        default=SiteFilterMode.DISABLED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="owned_sites")
    users: Mapped[list["SiteUser"]] = relationship(back_populates="site")
    geofences: Mapped[list["Geofence"]] = relationship(back_populates="site")
    ip_rules: Mapped[list["IPRule"]] = relationship(back_populates="site")
    audits: Mapped[list["AccessAudit"]] = relationship(back_populates="site")
    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="site")
