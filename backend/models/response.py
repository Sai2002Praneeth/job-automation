from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    """Response returned after a resume is stored successfully."""

    success: bool = True
    filename: str
    content_type: str
    size: int = Field(ge=0)
    saved_path: str


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
