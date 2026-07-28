"""Request-scoped job-description intelligence endpoints."""

from fastapi import APIRouter

from models.response import (
    JobAnalysisRequest, JobAnalysisResponse, JobProfileResponse, JobQualityResponse,
    JobQualityWarningResponse, JobStatisticsResponse,
)
from services.job_description_intelligence_service import JobDescriptionIntelligenceService


router = APIRouter(prefix="/api/job", tags=["job"])

def _service() -> JobDescriptionIntelligenceService:
    return JobDescriptionIntelligenceService()


def _quality_response(
    service: JobDescriptionIntelligenceService,
    request: JobAnalysisRequest,
) -> JobQualityResponse:
    """Translate service warning dataclasses into the declared API response type."""
    return JobQualityResponse(
        warnings=[
            JobQualityWarningResponse.model_validate(warning, from_attributes=True)
            for warning in service.get_quality_warnings(request.description, request.title)
        ]
    )

@router.post("/analyze", response_model=JobAnalysisResponse)
def analyze_job(request: JobAnalysisRequest) -> JobAnalysisResponse:
    """Return the complete deterministic intelligence view for a job description."""
    service = _service()
    return JobAnalysisResponse(
        profile=JobProfileResponse.model_validate(service.analyze(request.description, request.title), from_attributes=True),
        statistics=JobStatisticsResponse.model_validate(service.get_statistics(request.description, request.title), from_attributes=True),
        quality=_quality_response(service, request),
    )


@router.post("/profile", response_model=JobProfileResponse)
def get_job_profile(request: JobAnalysisRequest) -> JobProfileResponse:
    """Extract a normalized deterministic job profile without persistence."""
    return JobProfileResponse.model_validate(_service().analyze(request.description, request.title), from_attributes=True)


@router.post("/statistics", response_model=JobStatisticsResponse)
def get_job_statistics(request: JobAnalysisRequest) -> JobStatisticsResponse:
    """Return deterministic content statistics for a job description."""
    return JobStatisticsResponse.model_validate(_service().get_statistics(request.description, request.title), from_attributes=True)


@router.post("/quality", response_model=JobQualityResponse)
def get_job_quality(request: JobAnalysisRequest) -> JobQualityResponse:
    """Return explainable rule-based quality warnings for a job description."""
    return _quality_response(_service(), request)
