from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import pdfplumber

from utils.text_utils import (
    extract_section,
    find_email,
    find_name,
    find_phone,
    find_skills,
    normalize_text,
)

PDF_SIGNATURE = b"%PDF-"


class ResumeParserError(RuntimeError):
    """Base error raised by resume parsing operations."""


class InvalidPDFError(ResumeParserError):
    """Raised when the supplied file is not a readable PDF."""


class EmptyPDFError(ResumeParserError):
    """Raised when a PDF contains no extractable text."""


class ResumeParsingError(ResumeParserError):
    """Raised when text or fields cannot be extracted from a readable PDF."""


@dataclass(frozen=True)
class ParsedResume:
    """Framework-independent structured resume data."""

    raw_text: str
    name: str | None
    email: str | None
    phone: str | None
    skills: list[str]
    education: list[str]
    projects: list[str]
    experience: list[str]


class ResumeParser:
    """Extract text and common fields from resumes without external services."""

    def parse_pdf(self, source: BinaryIO | str | Path) -> ParsedResume:
        """Parse a PDF path or seekable binary stream into structured data."""
        if isinstance(source, (str, Path)):
            try:
                with Path(source).open("rb") as pdf_file:
                    return self.parse_pdf(pdf_file)
            except OSError as exc:
                raise InvalidPDFError("The PDF could not be opened.") from exc

        self._validate_pdf_signature(source)
        try:
            pdf = pdfplumber.open(source)
        except Exception as exc:
            raise InvalidPDFError("The uploaded file is not a readable PDF.") from exc

        try:
            with pdf:
                page_text = [page.extract_text() or "" for page in pdf.pages]
        except Exception as exc:
            raise ResumeParsingError("Text could not be extracted from the PDF.") from exc

        raw_text = normalize_text("\n\n".join(page_text))
        if not raw_text:
            raise EmptyPDFError("The PDF contains no extractable text.")
        return self.parse_text(raw_text)

    def parse_text(self, text: str) -> ParsedResume:
        """Parse already-extracted resume text into structured data."""
        raw_text = normalize_text(text)
        if not raw_text:
            raise EmptyPDFError("The resume text is empty.")

        try:
            return ParsedResume(
                raw_text=raw_text,
                name=find_name(raw_text),
                email=find_email(raw_text),
                phone=find_phone(raw_text),
                skills=find_skills(raw_text),
                education=extract_section(raw_text, "education"),
                projects=extract_section(raw_text, "projects"),
                experience=extract_section(raw_text, "experience"),
            )
        except Exception as exc:
            raise ResumeParsingError("The resume fields could not be parsed.") from exc

    @staticmethod
    def _validate_pdf_signature(source: BinaryIO) -> None:
        try:
            source.seek(0)
            header = source.read(1024)
            source.seek(0)
        except (OSError, ValueError) as exc:
            raise InvalidPDFError("The uploaded PDF could not be read.") from exc

        if PDF_SIGNATURE not in header:
            raise InvalidPDFError("The uploaded file is not a valid PDF.")


resume_parser = ResumeParser()
