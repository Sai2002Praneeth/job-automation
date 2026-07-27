from pathlib import Path
from typing import Annotated, BinaryIO, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from database.session import get_db
from models.response import (
    ResumeLibraryMetadataResponse,
    ResumeLibraryPageResponse,
    ResumeLibraryRenameRequest,
    ResumeLibraryResponse,
    ResumeParseResponse,
    ResumeProcessingResponse,
    ResumeUploadResponse,
    ResumeVersionResponse,
)
from repositories.resume_repository import ResumeRepository
from services.file_service import InvalidResumeError, ResumeStorageError, get_saved_resume_path, save_resume
from services.resume_parser import EmptyPDFError, InvalidPDFError, ParsedResume, ResumeParsingError, resume_parser
from services.resume_service import (
    InvalidResumeLibrarySelectionError,
    ResumeFileNotFoundError,
    ResumeLibraryConflictError,
    ResumeLibraryNotFoundError,
    ResumeNotFoundError,
    ResumeService,
)

router = APIRouter(prefix="/api/resume", tags=["resume"])
DatabaseSession = Annotated[Session, Depends(get_db)]
SortField = Literal["name", "created_at", "updated_at"]
SortOrder = Literal["asc", "desc"]


def get_resume_service(database_session: DatabaseSession) -> ResumeService:
    return ResumeService(ResumeRepository(database_session), resume_parser)


ResumeServiceDependency = Annotated[ResumeService, Depends(get_resume_service)]


@router.get("/libraries", response_model=list[ResumeLibraryResponse])
def list_resume_libraries(
    resume_service: ResumeServiceDependency,
    search: Annotated[str | None, Query(max_length=255)] = None,
    sort_by: SortField = "name",
    sort_order: SortOrder = "asc",
) -> list[ResumeLibraryResponse]:
    """Return the legacy list response, with optional search and sorting."""
    return [
        ResumeLibraryResponse.model_validate(library)
        for library in resume_service.list_resume_libraries(search, sort_by, sort_order)
    ]


@router.get("/libraries/page", response_model=ResumeLibraryPageResponse)
def list_resume_library_page(
    resume_service: ResumeServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=255)] = None,
    sort_by: SortField = "name",
    sort_order: SortOrder = "asc",
) -> ResumeLibraryPageResponse:
    """Return a paginated, searchable, and sorted resume library listing."""
    libraries, total = resume_service.list_resume_library_page(
        page, page_size, search, sort_by, sort_order
    )
    return ResumeLibraryPageResponse(
        items=[ResumeLibraryResponse.model_validate(library) for library in libraries],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/versions/{resume_id}/metadata", response_model=ResumeVersionResponse)
def get_resume_metadata(
    resume_service: ResumeServiceDependency,
    resume_id: int,
) -> ResumeVersionResponse:
    """Return persisted metadata for one resume version."""
    try:
        return ResumeVersionResponse.model_validate(resume_service.get_resume(resume_id))
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/versions/{resume_id}/download")
def download_resume(
    resume_service: ResumeServiceDependency,
    resume_id: int,
) -> FileResponse:
    """Download the original PDF for a stored resume version."""
    try:
        resume = resume_service.get_resume(resume_id)
        file_path = resume_service.get_resume_file_path(resume_id)
    except (ResumeNotFoundError, ResumeFileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FileResponse(file_path, media_type=resume.content_type, filename=resume.filename)


@router.get("/libraries/{resume_library_id}/metadata", response_model=ResumeLibraryMetadataResponse)
def get_resume_library_metadata(
    resume_service: ResumeServiceDependency,
    resume_library_id: int,
) -> ResumeLibraryMetadataResponse:
    """Return a library's details and version summary."""
    try:
        library, version_count, active_resume_id = resume_service.get_library_metadata(resume_library_id)
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResumeLibraryMetadataResponse(
        **ResumeLibraryResponse.model_validate(library).model_dump(),
        version_count=version_count,
        active_resume_id=active_resume_id,
    )


@router.put("/libraries/{resume_library_id}", response_model=ResumeLibraryResponse)
def rename_resume_library(
    resume_service: ResumeServiceDependency,
    resume_library_id: int,
    request: ResumeLibraryRenameRequest,
) -> ResumeLibraryResponse:
    """Rename a resume library without changing its versions."""
    try:
        library = resume_service.rename_resume_library(resume_library_id, request.name)
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (InvalidResumeLibrarySelectionError, ResumeLibraryConflictError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ResumeLibraryResponse.model_validate(library)


@router.delete("/libraries/{resume_library_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume_library(
    resume_service: ResumeServiceDependency,
    resume_library_id: int,
) -> Response:
    """Delete a library, its version records, and its managed files."""
    try:
        resume_service.delete_resume_library(resume_library_id)
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ResumeFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/libraries/{resume_library_id}/versions", response_model=list[ResumeVersionResponse])
def list_resume_library_versions(
    resume_service: ResumeServiceDependency,
    resume_library_id: int,
) -> list[ResumeVersionResponse]:
    """Return version history for a resume library entry."""
    try:
        versions = resume_service.list_library_versions(resume_library_id)
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [ResumeVersionResponse.model_validate(version) for version in versions]


@router.post(
    "/libraries/{resume_library_id}/versions/{resume_id}/restore",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def restore_resume_version(
    resume_service: ResumeServiceDependency,
    resume_library_id: int,
    resume_id: int,
) -> ResumeVersionResponse:
    """Restore an older version by creating a new active version."""
    try:
        resume = resume_service.restore_library_version(resume_library_id, resume_id)
    except (ResumeLibraryNotFoundError, ResumeNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResumeVersionResponse.model_validate(resume)


@router.get("/libraries/{resume_library_id}/active", response_model=ResumeVersionResponse)
def get_active_resume_version(
    resume_service: ResumeServiceDependency,
    resume_library_id: int,
) -> ResumeVersionResponse:
    """Return the active version for a resume library entry."""
    active_resume = resume_service.get_active_resume(resume_library_id)
    if active_resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active resume version was not found.")
    return ResumeVersionResponse.model_validate(active_resume)


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    resume_service: ResumeServiceDependency,
    file: UploadFile = File(...),
    resume_id: Annotated[int | None, Query(gt=0)] = None,
) -> ResumeParseResponse:
    """Extract text and structured fields from an uploaded PDF resume."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        await file.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")
    if file.content_type != "application/pdf":
        await file.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file must have the application/pdf content type.")
    try:
        parsed_resume = await _parse_pdf(file.file, resume_service)
        if resume_id is not None:
            try:
                resume_service.update_parsed_resume(resume_id, parsed_resume)
            except ResumeNotFoundError as exc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return ResumeParseResponse.model_validate(parsed_resume, from_attributes=True)
    finally:
        await file.close()


@router.post("/upload", response_model=ResumeProcessingResponse)
async def upload_resume(
    resume_service: ResumeServiceDependency,
    file: UploadFile = File(...),
    resume_library_id: Annotated[int | None, Form(gt=0)] = None,
    resume_library_name: Annotated[str | None, Form(max_length=255)] = None,
) -> ResumeProcessingResponse:
    """Validate, persist, parse, and version a PDF resume."""
    try:
        upload_response = await _save_resume(file)
        try:
            stored_resume = resume_service.persist_uploaded_resume(
                upload_response.filename, upload_response.content_type, upload_response.size,
                upload_response.saved_path, resume_library_id, resume_library_name,
            )
        except ResumeLibraryNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except InvalidResumeLibrarySelectionError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        upload_response.resume_id = stored_resume.id
        upload_response.resume_library_id = stored_resume.resume_library_id
        upload_response.resume_library_name = stored_resume.resume_library.name
        upload_response.version_number = stored_resume.version_number
        upload_response.is_active = stored_resume.is_active
        parsed_resume = await _parse_pdf(get_saved_resume_path(upload_response.filename), resume_service)
        resume_service.update_parsed_resume(stored_resume.id, parsed_resume)
    finally:
        await file.close()
    return ResumeProcessingResponse(
        upload=upload_response,
        parsed_resume=ResumeParseResponse.model_validate(parsed_resume, from_attributes=True),
    )


async def _save_resume(file: UploadFile) -> ResumeUploadResponse:
    try:
        filename, size, saved_path = await run_in_threadpool(save_resume, file)
    except InvalidResumeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ResumeStorageError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return ResumeUploadResponse(filename=filename, content_type=file.content_type or "application/pdf", size=size, saved_path=saved_path)


async def _parse_pdf(source: BinaryIO | str | Path, resume_service: ResumeService) -> ParsedResume:
    try:
        return await run_in_threadpool(resume_service.parse_pdf, source)
    except InvalidPDFError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmptyPDFError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except ResumeParsingError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

from models.response import (
    ResumeProfileResponse,
    ResumeQualityResponse,
    ResumeQualityWarningResponse,
    ResumeStatisticsResponse,
)
from services.resume_intelligence_service import ResumeIntelligenceService


def get_resume_intelligence_service(
    resume_service: ResumeServiceDependency,
) -> ResumeIntelligenceService:
    return ResumeIntelligenceService(resume_service)


ResumeIntelligenceServiceDependency = Annotated[
    ResumeIntelligenceService,
    Depends(get_resume_intelligence_service),
]


@router.get("/{resume_id}/profile", response_model=ResumeProfileResponse)
def get_resume_profile(
    resume_id: int,
    intelligence_service: ResumeIntelligenceServiceDependency,
) -> ResumeProfileResponse:
    """Return a normalized, deterministic profile for a resume version."""
    try:
        return ResumeProfileResponse.model_validate(
            intelligence_service.get_profile(resume_id), from_attributes=True
        )
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{resume_id}/statistics", response_model=ResumeStatisticsResponse)
def get_resume_statistics(
    resume_id: int,
    intelligence_service: ResumeIntelligenceServiceDependency,
) -> ResumeStatisticsResponse:
    """Return deterministic content and section statistics for a resume."""
    try:
        return ResumeStatisticsResponse.model_validate(
            intelligence_service.get_statistics(resume_id), from_attributes=True
        )
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{resume_id}/quality", response_model=ResumeQualityResponse)
def get_resume_quality(
    resume_id: int,
    intelligence_service: ResumeIntelligenceServiceDependency,
) -> ResumeQualityResponse:
    """Return explainable rule-based quality warnings for a resume."""
    try:
        return ResumeQualityResponse(
            resume_id=resume_id,
            warnings=[
                ResumeQualityWarningResponse.model_validate(warning, from_attributes=True)
                for warning in intelligence_service.get_quality_warnings(resume_id)
            ],
        )
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{resume_id}/normalized-skills", response_model=list[str])
def get_normalized_skills(
    resume_id: int,
    intelligence_service: ResumeIntelligenceServiceDependency,
) -> list[str]:
    """Return canonical skills with duplicate and alias values removed."""
    try:
        return intelligence_service.get_normalized_skills(resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
