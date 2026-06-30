from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile

UPLOAD_DIRECTORY = Path(__file__).resolve().parents[2] / "resume" / "originals"
PUBLIC_UPLOAD_DIRECTORY = Path("resume") / "originals"
COPY_CHUNK_SIZE = 1024 * 1024
PDF_SIGNATURE = b"%PDF-"
INVALID_FILENAME_CHARACTERS = frozenset('<>:"|?*')
RESERVED_WINDOWS_FILENAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
)


class InvalidResumeError(ValueError):
    """Raised when an uploaded file is not a valid PDF resume."""


class ResumeStorageError(RuntimeError):
    """Raised when a validated resume cannot be saved."""


def save_resume(upload: UploadFile) -> tuple[str, int, str]:
    """Validate and save an uploaded PDF, returning its storage metadata."""
    filename = _safe_filename(upload.filename)
    _validate_extension(filename)
    _validate_content_type(upload.content_type)
    _validate_pdf_signature(upload.file)

    try:
        UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
        saved_filename, size = _write_without_overwriting(upload.file, filename)
    except OSError as exc:
        raise ResumeStorageError("The resume could not be saved.") from exc

    saved_path = (PUBLIC_UPLOAD_DIRECTORY / saved_filename).as_posix()
    return saved_filename, size, saved_path


def _safe_filename(filename: str | None) -> str:
    if not filename:
        raise InvalidResumeError("A filename is required.")

    normalized_filename = filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    filename_stem = Path(normalized_filename).stem.upper()
    contains_invalid_character = any(
        character in INVALID_FILENAME_CHARACTERS or ord(character) < 32
        for character in normalized_filename
    )
    if (
        normalized_filename in {"", ".", ".."}
        or contains_invalid_character
        or filename_stem in RESERVED_WINDOWS_FILENAMES
    ):
        raise InvalidResumeError("The filename is invalid.")
    return normalized_filename


def _validate_extension(filename: str) -> None:
    if Path(filename).suffix.lower() != ".pdf":
        raise InvalidResumeError("Only PDF files are allowed.")


def _validate_content_type(content_type: str | None) -> None:
    if content_type != "application/pdf":
        raise InvalidResumeError("The uploaded file must have the application/pdf content type.")


def _validate_pdf_signature(source: BinaryIO) -> None:
    source.seek(0)
    header = source.read(1024)
    source.seek(0)
    if PDF_SIGNATURE not in header:
        raise InvalidResumeError("The uploaded file is not a valid PDF.")


def _write_without_overwriting(source: BinaryIO, filename: str) -> tuple[str, int]:
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    attempt = 0

    while True:
        saved_filename = filename if attempt == 0 else f"{stem}_{attempt}{suffix}"
        destination = UPLOAD_DIRECTORY / saved_filename
        try:
            with destination.open("xb") as target:
                return saved_filename, _copy_file(source, target)
        except FileExistsError:
            attempt += 1
            source.seek(0)
        except OSError:
            destination.unlink(missing_ok=True)
            raise


def _copy_file(source: BinaryIO, target: BinaryIO) -> int:
    size = 0
    while chunk := source.read(COPY_CHUNK_SIZE):
        target.write(chunk)
        size += len(chunk)
    return size
