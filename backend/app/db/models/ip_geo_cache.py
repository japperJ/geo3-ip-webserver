import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IpGeoCache(Base):
    __tablename__ = "ip_geo_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address: Mapped[str] = mapped_column(INET, unique=True, index=True, nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(10))
    location: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326))
    raw: Mapped[dict | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
