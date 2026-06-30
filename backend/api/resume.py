from fastapi import APIRouter, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from models.response import ResumeUploadResponse
from services.file_service import (
    InvalidResumeError,
    ResumeStorageError,
    save_resume,
)

router = APIRouter(prefix="/api/resume", tags=["resume"])


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
