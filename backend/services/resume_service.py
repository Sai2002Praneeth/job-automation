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
        '''Create or update metadata for a resume stored on disk.'''
        resume = self.resume_repository.get_by_path(resume_path)
        if resume is None:
            resume = Resume(
                filename=filename,
                content_type=content_type,
                file_size=file_size,
                resume_path=resume_path,
                raw_text='',
            )
            return self.resume_repository.create(resume)

        resume.filename = filename
        resume.content_type = content_type
        resume.file_size = file_size
        return self.resume_repository.update(resume)

    def persist_parsed_resume(
        self,
        parsed_resume: ParsedResume,
        resume_path: str,
    ) -> Resume:
        """Create or update the resume associated with a stored file."""
        resume = self.resume_repository.get_by_path(resume_path)
        if resume is None:
            resume = Resume(
                filename=Path(resume_path).name,
                content_type='application/pdf',
                file_size=0,
                resume_path=resume_path,
                location=None,
                raw_text=parsed_resume.raw_text,
            )

        self._apply_parsed_fields(resume, parsed_resume)
        if resume.id is None:
            return self.resume_repository.create(resume)
        return self.resume_repository.update(resume)

    def update_parsed_resume(
        self,
        resume_id: int,
        parsed_resume: ParsedResume,
    ) -> Resume:
        """Update parsed fields for an existing resume record."""
        resume = self.resume_repository.get_by_id(resume_id)
        if resume is None:
            raise ResumeNotFoundError(
                f"Resume with ID {resume_id} was not found."
            )

        self._apply_parsed_fields(resume, parsed_resume)
        return self.resume_repository.update(resume)

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
