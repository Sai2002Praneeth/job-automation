from fastapi import APIRouter, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from models.response import ResumeParseResponse, ResumeUploadResponse
from services.file_service import (
    InvalidResumeError,
    ResumeStorageError,
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
        parsed_resume = await run_in_threadpool(resume_parser.parse_pdf, file.file)
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
    finally:
        await file.close()

    return ResumeParseResponse(**vars(parsed_resume))


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    """Validate and persist a PDF resume."""
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
    finally:
        await file.close()

    return ResumeUploadResponse(
        filename=filename,
        content_type=file.content_type or "application/pdf",
        size=size,
        saved_path=saved_path,
    )
