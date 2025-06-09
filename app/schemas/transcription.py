from enum import Enum
from fastapi import File, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator


class ModelSize(str, Enum):
    tiny = "tiny"
    base = "base"
    small = "small"
    medium = "medium"
    large = "large"
    
class TranscriptionRequest(BaseModel):
    """Schema for video transcription request"""
    file: UploadFile = File(...),
    model_size: ModelSize = Field(
        default=ModelSize.base,
        description="Whisper model size: tiny, base, small, medium, or large",
    )
    
    @field_validator("file")
    def validate_file(cls, value):

        allowed_types = ["video/mp4", "video/avi"]
        print('value.content_type', value.content_type)
        if(value.content_type not in allowed_types):
            raise RequestValidationError(f"file must be one of: {', '.join(allowed_types)}")
        return value


class TranscriptionResponse(BaseModel):
    """Schema for transcription response"""
    video_path: str
    transcript: str
    transcript_id: str
    model_size: str
    success: bool


class ErrorResponse(BaseModel):
    """Schema for error response"""
    detail: str 