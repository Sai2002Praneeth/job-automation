from pathlib import Path
from typing import Annotated, BinaryIO

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from database.session import get_db
from models.response import (
    ResumeParseResponse,
    ResumeProcessingResponse,
    ResumeUploadResponse,
)
from repositories.resume_repository import ResumeRepository
from services.file_service import (
    InvalidResumeError,
    ResumeStorageError,
    get_saved_resume_path,
    save_resume,
)
from services.resume_parser import (
    EmptyPDFError,
    InvalidPDFError,
    ParsedResume,
    ResumeParsingError,
    resume_parser,
)
from services.resume_service import ResumeNotFoundError, ResumeService

router = APIRouter(prefix="/api/resume", tags=["resume"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_resume_service(database_session: DatabaseSession) -> ResumeService:
    return ResumeService(
        resume_repository=ResumeRepository(database_session),
        parser=resume_parser,
    )


ResumeServiceDependency = Annotated[
    ResumeService,
    Depends(get_resume_service),
]


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
)
async def parse_resume(
    resume_service: ResumeServiceDependency,
    file: UploadFile = File(...),
    resume_id: Annotated[int | None, Query(gt=0)] = None,
) -> ResumeParseResponse:
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
        parsed_resume = await _parse_pdf(file.file, resume_service)
        if resume_id is not None:
            try:
                resume_service.update_parsed_resume(resume_id, parsed_resume)
            except ResumeNotFoundError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(exc),
                ) from exc
        return ResumeParseResponse.model_validate(
            parsed_resume,
            from_attributes=True,
        )
    finally:
        await file.close()


@router.post(
    "/upload",
    response_model=ResumeProcessingResponse,
)
async def upload_resume(
    resume_service: ResumeServiceDependency,
    file: UploadFile = File(...),
) -> ResumeProcessingResponse:
    """Validate, persist, and parse a PDF resume."""
    try:
        upload_response = await _save_resume(file)
        stored_resume = resume_service.persist_uploaded_resume(
            filename=upload_response.filename,
            content_type=upload_response.content_type,
            file_size=upload_response.size,
            resume_path=upload_response.saved_path,
        )
        upload_response.resume_id = stored_resume.id
        upload_response.version_number = stored_resume.version_number
        upload_response.is_active = stored_resume.is_active
        parsed_resume = await _parse_pdf(
            get_saved_resume_path(upload_response.filename),
            resume_service,
        )
        resume_service.update_parsed_resume(
            stored_resume.id,
            parsed_resume,
        )
    finally:
        await file.close()

    return ResumeProcessingResponse(
        upload=upload_response,
        parsed_resume=ResumeParseResponse.model_validate(
            parsed_resume,
            from_attributes=True,
        ),
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


async def _parse_pdf(
    source: BinaryIO | str | Path,
    resume_service: ResumeService,
) -> ParsedResume:
    try:
        return await run_in_threadpool(resume_service.parse_pdf, source)
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

