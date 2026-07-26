from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.resume import Resume, ResumeLibrary


class ResumeRepository:
    """Provide persistence operations for resume libraries and versions."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def create_library(self, resume_library: ResumeLibrary) -> ResumeLibrary:
        self.database_session.add(resume_library)
        self.database_session.flush()
        return resume_library

    def get_library_by_id(
        self,
        resume_library_id: int,
    ) -> ResumeLibrary | None:
        return self.database_session.get(ResumeLibrary, resume_library_id)

    def get_library_by_name(self, name: str) -> ResumeLibrary | None:
        statement = select(ResumeLibrary).where(ResumeLibrary.name == name)
        return self.database_session.scalars(statement).first()

    def list_libraries(self) -> Sequence[ResumeLibrary]:
        statement = select(ResumeLibrary).order_by(ResumeLibrary.name)
        return self.database_session.scalars(statement).all()

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
            .order_by(Resume.id.desc())
        )
        return self.database_session.scalars(statement).first()

    def get_active(self) -> Resume | None:
        statement = (
            select(Resume)
            .where(Resume.is_active.is_(True))
            .order_by(Resume.updated_at.desc(), Resume.id.desc())
        )
        return self.database_session.scalars(statement).first()

    def get_active_by_library(self, resume_library_id: int) -> Resume | None:
        statement = (
            select(Resume)
            .where(
                Resume.resume_library_id == resume_library_id,
                Resume.is_active.is_(True),
            )
            .order_by(Resume.version_number.desc(), Resume.id.desc())
        )
        return self.database_session.scalars(statement).first()

    def get_latest_version_number(self, root_resume_id: int) -> int:
        statement = select(func.max(Resume.version_number)).where(
            Resume.root_resume_id == root_resume_id
        )
        return self.database_session.scalar(statement) or 0

    def get_latest_version_number_by_library(
        self,
        resume_library_id: int,
    ) -> int:
        statement = select(func.max(Resume.version_number)).where(
            Resume.resume_library_id == resume_library_id
        )
        return self.database_session.scalar(statement) or 0

    def list_versions(self, root_resume_id: int) -> Sequence[Resume]:
        statement = (
            select(Resume)
            .where(Resume.root_resume_id == root_resume_id)
            .order_by(Resume.version_number.desc(), Resume.id.desc())
        )
        return self.database_session.scalars(statement).all()

    def list_versions_by_library(
        self,
        resume_library_id: int,
    ) -> Sequence[Resume]:
        statement = (
            select(Resume)
            .where(Resume.resume_library_id == resume_library_id)
            .order_by(Resume.version_number.desc(), Resume.id.desc())
        )
        return self.database_session.scalars(statement).all()

    def list_all(self) -> Sequence[Resume]:
        statement = select(Resume).order_by(Resume.id)
        return self.database_session.scalars(statement).all()

    def update(self, resume: Resume) -> Resume:
        updated_resume = self.database_session.merge(resume)
        self.database_session.flush()
        return updated_resume

    def update_many(self, resumes: Sequence[Resume]) -> Sequence[Resume]:
        for resume in resumes:
            self.database_session.merge(resume)
        self.database_session.flush()
        return resumes

    def delete(self, resume: Resume) -> None:
        self.database_session.delete(resume)
        self.database_session.flush()
