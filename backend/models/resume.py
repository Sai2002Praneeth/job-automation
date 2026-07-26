from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.application import Application


class ResumeLibrary(Base):
    """A named resume entry that owns an independent version history."""

    __tablename__ = "resume_libraries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    resumes: Mapped[list[Resume]] = relationship(
        back_populates="resume_library"
    )


class Resume(Base):
    """A parsed resume version that can be used for job applications."""

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
    filename: Mapped[str] = mapped_column(String(255), default="")
    content_type: Mapped[str] = mapped_column(
        String(255),
        default="application/pdf",
    )
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    resume_path: Mapped[str] = mapped_column(String(1024))
    resume_library_id: Mapped[int] = mapped_column(
        ForeignKey("resume_libraries.id"),
        index=True,
    )
    root_resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resumes.id"),
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    resume_library: Mapped[ResumeLibrary] = relationship(
        back_populates="resumes"
    )
