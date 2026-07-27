from pathlib import Path
from typing import BinaryIO, Literal

from models.resume import Resume, ResumeLibrary
from repositories.resume_repository import ResumeRepository
from services.file_service import ResumeStorageError, get_stored_resume_path
from services.resume_parser import ParsedResume, ResumeParser


LibrarySortField = Literal["name", "created_at", "updated_at"]
SortOrder = Literal["asc", "desc"]


class ResumeNotFoundError(LookupError):
    """Raised when a requested resume record does not exist."""


class ResumeLibraryNotFoundError(LookupError):
    """Raised when a requested resume library entry does not exist."""


class InvalidResumeLibrarySelectionError(ValueError):
    """Raised when a resume library selection is invalid."""


class ResumeLibraryConflictError(ValueError):
    """Raised when a requested library change conflicts with an existing one."""


class ResumeFileNotFoundError(FileNotFoundError):
    """Raised when a stored resume file cannot be accessed."""


class ResumeService:
    """Coordinate resume parsing, versioning, and library management."""

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
            filename, resume_library_id, resume_library_name
        )
        return self._create_active_version(
            resume_library, filename, content_type, file_size, resume_path
        )

    def persist_parsed_resume(self, parsed_resume: ParsedResume, resume_path: str) -> Resume:
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

    def update_parsed_resume(self, resume_id: int, parsed_resume: ParsedResume) -> Resume:
        """Update parsed fields for an existing resume version."""
        resume = self.get_resume(resume_id)
        self._apply_parsed_fields(resume, parsed_resume)
        return self.resume_repository.update(resume)

    def get_resume(self, resume_id: int) -> Resume:
        """Return a resume version or raise a domain-specific error."""
        resume = self.resume_repository.get_by_id(resume_id)
        if resume is None:
            raise ResumeNotFoundError(f"Resume with ID {resume_id} was not found.")
        return resume

    def get_resume_file_path(self, resume_id: int) -> Path:
        """Return the managed PDF file for a stored resume version."""
        resume = self.get_resume(resume_id)
        try:
            file_path = get_stored_resume_path(resume.resume_path)
        except ResumeStorageError as exc:
            raise ResumeFileNotFoundError("The stored resume file is unavailable.") from exc
        if not file_path.is_file():
            raise ResumeFileNotFoundError("The stored resume file is unavailable.")
        return file_path

    def get_active_resume(self, resume_library_id: int | None = None) -> Resume | None:
        """Return an active resume version, if one exists."""
        if resume_library_id is None:
            return self.resume_repository.get_active()
        return self.resume_repository.get_active_by_library(resume_library_id)

    def list_resume_libraries(
        self,
        search: str | None = None,
        sort_by: LibrarySortField = "name",
        sort_order: SortOrder = "asc",
    ) -> list[ResumeLibrary]:
        """Return searchable and sorted resume library entries."""
        normalized_search = self._normalize_search(search)
        return list(self.resume_repository.list_libraries(normalized_search, sort_by, sort_order))

    def list_resume_library_page(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        sort_by: LibrarySortField = "name",
        sort_order: SortOrder = "asc",
    ) -> tuple[list[ResumeLibrary], int]:
        """Return one searchable, sorted page and its total size."""
        normalized_search = self._normalize_search(search)
        total = self.resume_repository.count_libraries(normalized_search)
        libraries = self.resume_repository.list_libraries(
            normalized_search, sort_by, sort_order, (page - 1) * page_size, page_size
        )
        return list(libraries), total

    def get_library_metadata(self, resume_library_id: int) -> tuple[ResumeLibrary, int, int | None]:
        """Return a library with its version count and active version ID."""
        library = self._get_library(resume_library_id)
        versions = self.resume_repository.list_versions_by_library(resume_library_id)
        active_resume = next((version for version in versions if version.is_active), None)
        return library, len(versions), active_resume.id if active_resume else None

    def rename_resume_library(self, resume_library_id: int, name: str) -> ResumeLibrary:
        """Rename a resume library while preserving its version history."""
        library = self._get_library(resume_library_id)
        normalized_name = self._normalize_library_name(name)
        assert normalized_name is not None
        existing = self.resume_repository.get_library_by_name(normalized_name)
        if existing is not None and existing.id != library.id:
            raise ResumeLibraryConflictError("A resume library with this name already exists.")
        library.name = normalized_name
        return self.resume_repository.update_library(library)

    def delete_resume_library(self, resume_library_id: int) -> None:
        """Delete a library and all of its version records and managed files."""
        library = self._get_library(resume_library_id)
        versions = list(self.resume_repository.list_versions_by_library(library.id))
        paths = {self._managed_file_path(version) for version in versions}
        staged_paths = self._stage_files_for_deletion(paths)
        try:
            self.resume_repository.delete_library_transactionally(library)
        except Exception:
            self._restore_staged_files(staged_paths)
            raise
        for staged_path in staged_paths.values():
            staged_path.unlink(missing_ok=True)

    def list_resume_versions(self, root_resume_id: int) -> list[Resume]:
        """Return all versions for a legacy resume history."""
        return list(self.resume_repository.list_versions(root_resume_id))

    def list_library_versions(self, resume_library_id: int) -> list[Resume]:
        """Return all versions for a resume library entry."""
        self._get_library(resume_library_id)
        return list(self.resume_repository.list_versions_by_library(resume_library_id))

    def restore_library_version(self, resume_library_id: int, resume_id: int) -> Resume:
        """Create a new active version from an older library version."""
        library = self._get_library(resume_library_id)
        source = self.resume_repository.get_by_id_for_library(resume_id, library.id)
        if source is None:
            raise ResumeNotFoundError(f"Resume with ID {resume_id} was not found in this library.")
        return self._create_active_version(
            library, source.filename, source.content_type, source.file_size,
            source.resume_path, source,
        )

    def _resolve_resume_library(self, filename: str, resume_library_id: int | None, resume_library_name: str | None) -> ResumeLibrary:
        if resume_library_id is not None and resume_library_name is not None:
            raise InvalidResumeLibrarySelectionError("Use either resume_library_id or resume_library_name, not both.")
        if resume_library_id is not None:
            return self._get_library(resume_library_id)
        normalized_name = self._normalize_library_name(resume_library_name)
        if normalized_name is not None:
            existing_library = self.resume_repository.get_library_by_name(normalized_name)
            return existing_library or self.resume_repository.create_library(ResumeLibrary(name=normalized_name))
        active_resume = self.resume_repository.get_active()
        if active_resume is not None:
            return active_resume.resume_library
        default_name = self._default_library_name(filename)
        existing_default = self.resume_repository.get_library_by_name(default_name)
        return existing_default or self.resume_repository.create_library(ResumeLibrary(name=default_name))

    def _create_active_version(
        self, resume_library: ResumeLibrary, filename: str, content_type: str,
        file_size: int, resume_path: str, source: Resume | None = None,
    ) -> Resume:
        active_resume = self.resume_repository.get_active_by_library(resume_library.id)
        version_number = self.resume_repository.get_latest_version_number_by_library(resume_library.id) + 1
        versions = self.resume_repository.list_versions_by_library(resume_library.id)
        for version in versions:
            version.is_active = False
        self.resume_repository.update_many(versions)
        root_resume_id = (active_resume.root_resume_id or active_resume.id) if active_resume else None
        resume = Resume(
            filename=filename, content_type=content_type, file_size=file_size,
            resume_path=resume_path, raw_text=source.raw_text if source else "",
            resume_library_id=resume_library.id, root_resume_id=root_resume_id,
            version_number=version_number, is_active=True,
            full_name=source.full_name if source else None,
            email=source.email if source else None,
            phone=source.phone if source else None,
            location=source.location if source else None,
            skills=list(source.skills) if source else [],
            education=list(source.education) if source else [],
            projects=list(source.projects) if source else [],
            experience=list(source.experience) if source else [],
        )
        created_resume = self.resume_repository.create(resume)
        if created_resume.root_resume_id is None:
            created_resume.root_resume_id = created_resume.id
            return self.resume_repository.update(created_resume)
        return created_resume

    def _get_library(self, resume_library_id: int) -> ResumeLibrary:
        library = self.resume_repository.get_library_by_id(resume_library_id)
        if library is None:
            raise ResumeLibraryNotFoundError(f"Resume library with ID {resume_library_id} was not found.")
        return library

    @staticmethod
    def _normalize_library_name(name: str | None) -> str | None:
        if name is None:
            return None
        normalized_name = " ".join(name.split())
        if not normalized_name:
            raise InvalidResumeLibrarySelectionError("Resume library name cannot be empty.")
        if len(normalized_name) > 255:
            raise InvalidResumeLibrarySelectionError("Resume library name cannot exceed 255 characters.")
        return normalized_name

    @staticmethod
    def _normalize_search(search: str | None) -> str | None:
        return " ".join(search.split()) if search and search.strip() else None

    @staticmethod
    def _default_library_name(filename: str) -> str:
        stem = Path(filename).stem.strip()
        return stem[:255] if stem else "Default Resume"

    @staticmethod
    def _apply_parsed_fields(resume: Resume, parsed_resume: ParsedResume) -> None:
        resume.full_name = parsed_resume.name
        resume.email = parsed_resume.email
        resume.phone = parsed_resume.phone
        resume.raw_text = parsed_resume.raw_text
        resume.skills = list(parsed_resume.skills)
        resume.education = list(parsed_resume.education)
        resume.projects = list(parsed_resume.projects)
        resume.experience = list(parsed_resume.experience)

    @staticmethod
    def _managed_file_path(resume: Resume) -> Path:
        try:
            return get_stored_resume_path(resume.resume_path)
        except ResumeStorageError as exc:
            raise ResumeFileNotFoundError("The stored resume file is unavailable.") from exc

    @staticmethod
    def _stage_files_for_deletion(paths: set[Path]) -> dict[Path, Path]:
        staged_paths: dict[Path, Path] = {}
        for path in paths:
            if not path.exists():
                continue
            staged_path = path.with_name(f".{path.name}.deleting")
            suffix = 1
            while staged_path.exists():
                staged_path = path.with_name(f".{path.name}.deleting.{suffix}")
                suffix += 1
            path.replace(staged_path)
            staged_paths[path] = staged_path
        return staged_paths

    @staticmethod
    def _restore_staged_files(staged_paths: dict[Path, Path]) -> None:
        for original_path, staged_path in staged_paths.items():
            if staged_path.exists():
                staged_path.replace(original_path)

