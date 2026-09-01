import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    service_type: Mapped[str] = mapped_column(String(60), index=True)
    region: Mapped[str] = mapped_column(String(60), index=True)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    rating: Mapped[float] = mapped_column(Float)
    base_response_speed: Mapped[float] = mapped_column(Float)
    profile_text: Mapped[str] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(30))
    years_experience: Mapped[int] = mapped_column(default=1)
    avatar_url: Mapped[str | None] = mapped_column(String(300))
    service_areas: Mapped[str | None] = mapped_column(String(500))
    reliability_alpha: Mapped[float] = mapped_column(Float, default=1.0)
    reliability_beta: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
