import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SiteFilterMode(str, enum.Enum):
    ALLOWLIST = "allowlist"
    BLOCKLIST = "blocklist"
    DISABLED = "disabled"


class SiteUserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


class IPRuleAction(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"


class AccessDecision(str, enum.Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    owned_sites: Mapped[list["Site"]] = relationship(back_populates="owner")
    site_links: Mapped[list["SiteUser"]] = relationship(back_populates="user")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255), index=True, unique=True)
    path_prefix: Mapped[str] = mapped_column(String(255), default="/", nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    filter_mode: Mapped[SiteFilterMode] = mapped_column(
        Enum(SiteFilterMode, name="site_filter_mode", native_enum=False),
        default=SiteFilterMode.ALLOWLIST,
        nullable=False,
    )
    block_page_title: Mapped[str] = mapped_column(
        String(255), default="Access Denied", nullable=False
    )
    block_page_message: Mapped[str] = mapped_column(
        Text,
        default="Your location or IP address does not meet the access requirements for this site.",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    owner: Mapped[User] = relationship(back_populates="owned_sites")
    users: Mapped[list["SiteUser"]] = relationship(back_populates="site")
    geofences: Mapped[list["Geofence"]] = relationship(back_populates="site")
    ip_rules: Mapped[list["IPRule"]] = relationship(back_populates="site")
    audits: Mapped[list["AccessAudit"]] = relationship(back_populates="site")
    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="site")


class SiteUser(Base):
    __tablename__ = "site_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False
    )
    role: Mapped[SiteUserRole] = mapped_column(
        Enum(SiteUserRole, name="site_user_role", native_enum=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="site_links")
    site: Mapped[Site] = relationship(back_populates="users")


class Geofence(Base):
    __tablename__ = "geofences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255))
    polygon: Mapped[object | None] = mapped_column(Geometry("POLYGON", srid=4326))
    center: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326))
    radius_meters: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    site: Mapped[Site] = relationship(back_populates="geofences")


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
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    site: Mapped[Site] = relationship(back_populates="ip_rules")


class AccessAudit(Base):
    __tablename__ = "access_audit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    client_ip: Mapped[str | None] = mapped_column(String(50))
    ip_geo_country: Mapped[str | None] = mapped_column(String(10))
    ip_geo_city: Mapped[str | None] = mapped_column(String(100))
    ip_geo_point: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326))
    client_gps_point: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326))
    decision: Mapped[AccessDecision | None] = mapped_column(
        Enum(AccessDecision, name="access_decision", native_enum=False)
    )
    reason: Mapped[str | None] = mapped_column(String(500))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    artifact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    site: Mapped[Site] = relationship(back_populates="audits")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False
    )
    audit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    site: Mapped[Site] = relationship(back_populates="artifacts")


class IpGeoCache(Base):
    __tablename__ = "ip_geo_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address: Mapped[str] = mapped_column(INET, unique=True, index=True, nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(10))
    city: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    location: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326))
    raw: Mapped[dict | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
