from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.resume import Resume


class ResumeRepository:
    """Provide persistence operations for resumes."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def create(self, resume: Resume) -> Resume:
        self.database_session.add(resume)
        self.database_session.flush()
        return resume

    def get_by_id(self, resume_id: int) -> Resume | None:
        return self.database_session.get(Resume, resume_id)

    def get_by_path(self, resume_path: str) -> Resume | None:
        statement = (
            select(Resume)
            .where(Resume.resume_path == resume_path)
            .order_by(Resume.id)
        )
        return self.database_session.scalars(statement).first()

    def list_all(self) -> Sequence[Resume]:
        statement = select(Resume).order_by(Resume.id)
        return self.database_session.scalars(statement).all()

    def update(self, resume: Resume) -> Resume:
        updated_resume = self.database_session.merge(resume)
        self.database_session.flush()
        return updated_resume

    def delete(self, resume: Resume) -> None:
        self.database_session.delete(resume)
        self.database_session.flush()
