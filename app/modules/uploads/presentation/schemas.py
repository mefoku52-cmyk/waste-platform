"""uploads API schemas."""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    fileId: str = Field(..., description="Internal file identifier")
    url: str = Field(..., description="Authenticated retrieval URL")
    originalName: str = Field(..., description="Original uploaded filename")
    size: int = Field(..., ge=0, description="Stored file size in bytes")
    contentType: str | None = Field(default=None, description="Detected or supplied content type")


class UploadErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict | list | str | None = None
    request_id: str | None = None
