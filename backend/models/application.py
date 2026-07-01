from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.job import Job
    from models.resume import Resume


class Application(Base):
    """A resume's application to a job."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    status: Mapped[str] = mapped_column(String(100))
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    resume: Mapped[Resume] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")
