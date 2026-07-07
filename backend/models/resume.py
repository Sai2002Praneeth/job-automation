from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.application import Application


class Resume(Base):
    """A parsed resume that can be used for job applications."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    education: Mapped[list[str]] = mapped_column(JSON, default=list)
    projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience: Mapped[list[str]] = mapped_column(JSON, default=list)
    filename: Mapped[str] = mapped_column(String(255), default='')
    content_type: Mapped[str] = mapped_column(
        String(255),
        default='application/pdf',
    )
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    resume_path: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    applications: Mapped[list[Application]] = relationship(
        back_populates="resume"
    )
