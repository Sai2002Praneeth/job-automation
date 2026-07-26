from pathlib import Path
from typing import BinaryIO

from models.resume import Resume, ResumeLibrary
from repositories.resume_repository import ResumeRepository
from services.resume_parser import ParsedResume, ResumeParser


class ResumeNotFoundError(LookupError):
    """Raised when a requested resume record does not exist."""


class ResumeLibraryNotFoundError(LookupError):
    """Raised when a requested resume library entry does not exist."""


class InvalidResumeLibrarySelectionError(ValueError):
    """Raised when a resume library selection is invalid."""


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
        resume_library_id: int | None = None,
        resume_library_name: str | None = None,
    ) -> Resume:
        """Create a new active resume version for a stored upload."""
        resume_library = self._resolve_resume_library(
            filename=filename,
            resume_library_id=resume_library_id,
            resume_library_name=resume_library_name,
        )
        return self._create_active_version(
            resume_library=resume_library,
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
            resume = self.persist_uploaded_resume(
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

    def get_active_resume(
        self,
        resume_library_id: int | None = None,
    ) -> Resume | None:
        """Return an active resume version, if one exists."""
        if resume_library_id is None:
            return self.resume_repository.get_active()
        return self.resume_repository.get_active_by_library(resume_library_id)

    def list_resume_libraries(self) -> list[ResumeLibrary]:
        """Return all resume library entries."""
        return list(self.resume_repository.list_libraries())

    def list_resume_versions(self, root_resume_id: int) -> list[Resume]:
        """Return all versions for a legacy resume history."""
        return list(self.resume_repository.list_versions(root_resume_id))

    def list_library_versions(self, resume_library_id: int) -> list[Resume]:
        """Return all versions for a resume library entry."""
        resume_library = self.resume_repository.get_library_by_id(
            resume_library_id
        )
        if resume_library is None:
            raise ResumeLibraryNotFoundError(
                f"Resume library with ID {resume_library_id} was not found."
            )
        return list(
            self.resume_repository.list_versions_by_library(resume_library_id)
        )

    def _resolve_resume_library(
        self,
        filename: str,
        resume_library_id: int | None,
        resume_library_name: str | None,
    ) -> ResumeLibrary:
        if resume_library_id is not None and resume_library_name is not None:
            raise InvalidResumeLibrarySelectionError(
                "Use either resume_library_id or resume_library_name, not both."
            )

        if resume_library_id is not None:
            resume_library = self.resume_repository.get_library_by_id(
                resume_library_id
            )
            if resume_library is None:
                raise ResumeLibraryNotFoundError(
                    f"Resume library with ID {resume_library_id} was not found."
                )
            return resume_library

        normalized_name = self._normalize_library_name(resume_library_name)
        if normalized_name is not None:
            existing_library = self.resume_repository.get_library_by_name(
                normalized_name
            )
            if existing_library is not None:
                return existing_library
            return self.resume_repository.create_library(
                ResumeLibrary(name=normalized_name)
            )

        active_resume = self.resume_repository.get_active()
        if active_resume is not None:
            return active_resume.resume_library

        default_name = self._default_library_name(filename)
        existing_default = self.resume_repository.get_library_by_name(
            default_name
        )
        if existing_default is not None:
            return existing_default

        return self.resume_repository.create_library(
            ResumeLibrary(name=default_name)
        )

    def _create_active_version(
        self,
        resume_library: ResumeLibrary,
        filename: str,
        content_type: str,
        file_size: int,
        resume_path: str,
    ) -> Resume:
        active_resume = self.resume_repository.get_active_by_library(
            resume_library.id
        )
        version_number = (
            self.resume_repository.get_latest_version_number_by_library(
                resume_library.id
            )
            + 1
        )

        versions = self.resume_repository.list_versions_by_library(
            resume_library.id
        )
        for version in versions:
            version.is_active = False
        self.resume_repository.update_many(versions)

        root_resume_id = None
        if active_resume is not None:
            root_resume_id = active_resume.root_resume_id or active_resume.id

        resume = Resume(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            resume_path=resume_path,
            raw_text="",
            resume_library_id=resume_library.id,
            root_resume_id=root_resume_id,
            version_number=version_number,
            is_active=True,
        )
        created_resume = self.resume_repository.create(resume)
        if created_resume.root_resume_id is None:
            created_resume.root_resume_id = created_resume.id
            return self.resume_repository.update(created_resume)
        return created_resume

    @staticmethod
    def _normalize_library_name(name: str | None) -> str | None:
        if name is None:
            return None

        normalized_name = " ".join(name.split())
        if not normalized_name:
            raise InvalidResumeLibrarySelectionError(
                "Resume library name cannot be empty."
            )
        if len(normalized_name) > 255:
            raise InvalidResumeLibrarySelectionError(
                "Resume library name cannot exceed 255 characters."
            )
        return normalized_name

    @staticmethod
    def _default_library_name(filename: str) -> str:
        stem = Path(filename).stem.strip()
        if stem:
            return stem[:255]
        return "Default Resume"

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
