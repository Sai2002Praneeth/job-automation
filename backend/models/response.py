from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeUploadResponse(BaseModel):
    """Response returned after a resume is stored successfully."""

    success: bool = True
    filename: str
    content_type: str
    size: int = Field(ge=0)
    saved_path: str
    resume_id: int | None = None
    resume_library_id: int | None = None
    resume_library_name: str | None = None
    version_number: int | None = None
    is_active: bool | None = None


class ResumeParseResponse(BaseModel):
    """Structured fields extracted from an uploaded resume."""

    raw_text: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)


class ResumeVersionResponse(BaseModel):
    """A stored resume version."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_library_id: int
    root_resume_id: int | None = None
    version_number: int
    is_active: bool
    filename: str
    content_type: str
    file_size: int = Field(ge=0)
    resume_path: str
    created_at: datetime
    updated_at: datetime


class ResumeLibraryResponse(BaseModel):
    """A named resume library entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime


class ResumeLibraryMetadataResponse(ResumeLibraryResponse):
    """Resume library details with its version summary."""

    version_count: int = Field(ge=0)
    active_resume_id: int | None = None


class ResumeLibraryPageResponse(BaseModel):
    """A searchable, sorted page of resume libraries."""

    items: list[ResumeLibraryResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class ResumeLibraryRenameRequest(BaseModel):
    """Request payload for changing a resume library name."""

    name: str = Field(min_length=1, max_length=255)


class ResumeProcessingResponse(BaseModel):
    """Combined upload metadata and parsed resume data."""

    upload: ResumeUploadResponse
    parsed_resume: ResumeParseResponse

class ResumeSectionResponse(BaseModel):
    """Detection status for a standard resume section."""

    name: str
    detected: bool


class ResumeCompletenessResponse(BaseModel):
    """Explainable completion assessment for a resume."""

    score: int = Field(ge=0, le=100)
    present_fields: list[str]
    missing_fields: list[str]


class ResumeProfileResponse(BaseModel):
    """Normalized profile generated from persisted parsed resume data."""

    resume_id: int
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str]
    sections: list[ResumeSectionResponse]
    completeness: ResumeCompletenessResponse


class ResumeStatisticsResponse(BaseModel):
    """Deterministic statistics for a stored resume."""

    word_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    line_count: int = Field(ge=0)
    skill_count: int = Field(ge=0)
    normalized_skill_count: int = Field(ge=0)
    duplicate_skill_count: int = Field(ge=0)
    detected_section_count: int = Field(ge=0)


class ResumeQualityWarningResponse(BaseModel):
    """A deterministic and actionable resume quality warning."""

    code: str
    severity: str
    message: str


class ResumeQualityResponse(BaseModel):
    """Quality warnings generated from deterministic resume rules."""

    resume_id: int
    warnings: list[ResumeQualityWarningResponse]


class JobAnalysisRequest(BaseModel):
    """Unpersisted job description supplied for deterministic analysis."""

    description: str = Field(min_length=1, max_length=100_000)
    title: str | None = Field(default=None, max_length=255)


class JobExperienceResponse(BaseModel):
    minimum_years: int | None = Field(default=None, ge=0)
    maximum_years: int | None = Field(default=None, ge=0)
    requirements: list[str]


class JobEducationResponse(BaseModel):
    degrees: list[str]
    fields: list[str]


class JobLocationResponse(BaseModel):
    locations: list[str]
    remote_type: str | None = None


class JobSalaryResponse(BaseModel):
    raw_text: str | None = None
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    currency: str | None = None
    period: str | None = None


class JobEmploymentResponse(BaseModel):
    employment_types: list[str]
    remote_type: str | None = None


class JobProfileResponse(BaseModel):
    """Normalized profile extracted from a job description."""

    title: str | None = None
    required_skills: list[str]
    preferred_skills: list[str]
    experience: JobExperienceResponse
    education: JobEducationResponse
    location: JobLocationResponse
    salary: JobSalaryResponse
    employment: JobEmploymentResponse
    responsibilities: list[str]


class JobStatisticsResponse(BaseModel):
    word_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    line_count: int = Field(ge=0)
    required_skill_count: int = Field(ge=0)
    preferred_skill_count: int = Field(ge=0)
    responsibility_count: int = Field(ge=0)
    experience_requirement_count: int = Field(ge=0)


class JobQualityWarningResponse(BaseModel):
    code: str
    severity: str
    message: str


class JobQualityResponse(BaseModel):
    warnings: list[JobQualityWarningResponse]


class JobAnalysisResponse(BaseModel):
    profile: JobProfileResponse
    statistics: JobStatisticsResponse
    quality: JobQualityResponse
