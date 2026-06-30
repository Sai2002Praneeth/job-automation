from pathlib import Path
from typing import BinaryIO

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from models.response import (
    ResumeParseResponse,
    ResumeProcessingResponse,
    ResumeUploadResponse,
)
from services.file_service import (
    InvalidResumeError,
    ResumeStorageError,
    get_saved_resume_path,
    save_resume,
)
from services.resume_parser import (
    EmptyPDFError,
    InvalidPDFError,
    ResumeParsingError,
    resume_parser,
)

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
)
async def parse_resume(file: UploadFile = File(...)) -> ResumeParseResponse:
    """Extract text and structured fields from an uploaded PDF resume."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        await file.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed.",
        )
    if file.content_type != "application/pdf":
        await file.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must have the application/pdf content type.",
        )

    try:
        return await _parse_pdf(file.file)
    finally:
        await file.close()


@router.post(
    "/upload",
    response_model=ResumeProcessingResponse,
)
async def upload_resume(file: UploadFile = File(...)) -> ResumeProcessingResponse:
    """Validate, persist, and parse a PDF resume."""
    try:
        upload_response = await _save_resume(file)
        parsed_resume = await _parse_pdf(
            get_saved_resume_path(upload_response.filename)
        )
    finally:
        await file.close()

    return ResumeProcessingResponse(
        upload=upload_response,
        parsed_resume=parsed_resume,
    )


async def _save_resume(file: UploadFile) -> ResumeUploadResponse:
    try:
        filename, size, saved_path = await run_in_threadpool(save_resume, file)
    except InvalidResumeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ResumeStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return ResumeUploadResponse(
        filename=filename,
        content_type=file.content_type or "application/pdf",
        size=size,
        saved_path=saved_path,
    )


async def _parse_pdf(source: BinaryIO | str | Path) -> ResumeParseResponse:
    try:
        parsed_resume = await run_in_threadpool(resume_parser.parse_pdf, source)
    except InvalidPDFError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except EmptyPDFError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ResumeParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return ResumeParseResponse.model_validate(parsed_resume, from_attributes=True)
