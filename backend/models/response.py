from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    """Response returned after a resume is stored successfully."""

    success: bool = True
    filename: str
    content_type: str
    size: int = Field(ge=0)
    saved_path: str
