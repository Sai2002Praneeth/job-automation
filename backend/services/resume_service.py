from pathlib import Path
from typing import BinaryIO

from models.resume import Resume
from repositories.resume_repository import ResumeRepository
from services.resume_parser import ParsedResume, ResumeParser


class ResumeNotFoundError(LookupError):
    """Raised when a requested resume record does not exist."""


class ResumeService:
    """Coordinate resume parsing and persistence."""

    def __init__(
        self,
        resume_repository: ResumeRepository,
        parser: ResumeParser,
    ) -> None:
        self.resume_repository = resume_repository
        self.parser = parser

    def parse_pdf(self, source: BinaryIO | str | Path) -> ParsedResume:
        """Parse a PDF independently of upload and persistence."""
        return self.parser.parse_pdf(source)

    def persist_uploaded_resume(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        resume_path: str,
    ) -> Resume:
        """Create a new active resume version for a stored upload."""
        return self._create_active_version(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            resume_path=resume_path,
        )

    def persist_parsed_resume(
        self,
        parsed_resume: ParsedResume,
        resume_path: str,
    ) -> Resume:
        """Persist parsed fields against the version for a stored file."""
        resume = self.resume_repository.get_by_path(resume_path)
        if resume is None:
            resume = self._create_active_version(
                filename=Path(resume_path).name,
                content_type="application/pdf",
                file_size=0,
                resume_path=resume_path,
            )

        self._apply_parsed_fields(resume, parsed_resume)
        return self.resume_repository.update(resume)

    def update_parsed_resume(
        self,
        resume_id: int,
        parsed_resume: ParsedResume,
    ) -> Resume:
        """Update parsed fields for an existing resume version."""
        resume = self.resume_repository.get_by_id(resume_id)
        if resume is None:
            raise ResumeNotFoundError(
                f"Resume with ID {resume_id} was not found."
            )

        self._apply_parsed_fields(resume, parsed_resume)
        return self.resume_repository.update(resume)

    def get_active_resume(self) -> Resume | None:
        """Return the active resume version, if one exists."""
        return self.resume_repository.get_active()

    def list_resume_versions(self, root_resume_id: int) -> list[Resume]:
        """Return all versions for a resume history."""
        return list(self.resume_repository.list_versions(root_resume_id))

    def _create_active_version(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        resume_path: str,
    ) -> Resume:
        active_resume = self.resume_repository.get_active()
        if active_resume is None:
            resume = Resume(
                filename=filename,
                content_type=content_type,
                file_size=file_size,
                resume_path=resume_path,
                raw_text="",
                version_number=1,
                is_active=True,
            )
            created_resume = self.resume_repository.create(resume)
            created_resume.root_resume_id = created_resume.id
            return self.resume_repository.update(created_resume)

        root_resume_id = active_resume.root_resume_id or active_resume.id
        version_number = (
            self.resume_repository.get_latest_version_number(root_resume_id)
            + 1
        )
        versions = self.resume_repository.list_versions(root_resume_id)
        for version in versions:
            version.is_active = False
        self.resume_repository.update_many(versions)

        resume = Resume(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            resume_path=resume_path,
            raw_text="",
            root_resume_id=root_resume_id,
            version_number=version_number,
            is_active=True,
        )
        return self.resume_repository.create(resume)

    @staticmethod
    def _apply_parsed_fields(
        resume: Resume,
        parsed_resume: ParsedResume,
    ) -> None:
        resume.full_name = parsed_resume.name
        resume.email = parsed_resume.email
        resume.phone = parsed_resume.phone
        resume.raw_text = parsed_resume.raw_text
        resume.skills = list(parsed_resume.skills)
        resume.education = list(parsed_resume.education)
        resume.projects = list(parsed_resume.projects)
        resume.experience = list(parsed_resume.experience)
