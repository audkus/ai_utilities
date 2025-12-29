"""File-related models for AI provider file operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class UploadedFile(BaseModel):
    """Represents a file uploaded to an AI provider.
    
    This model standardizes the response from different providers' file upload APIs.
    """
    
    # Required fields
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    filename: str = Field(..., description="Original filename of the uploaded file")
    bytes: int = Field(..., description="Size of the file in bytes")
    provider: str = Field(..., description="Name of the provider that stores the file")
    
    # Optional fields
    purpose: Optional[str] = Field(
        None, description="Purpose of the uploaded file (e.g., 'assistants', 'fine-tune')"
    )
    created_at: Optional[datetime] = Field(
        None, description="When the file was uploaded"
    )
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    def __str__(self) -> str:
        """String representation showing file ID and filename."""
        return (
            f"UploadedFile(id={self.file_id}, filename={self.filename}, "
            f"provider={self.provider})"
        )
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"UploadedFile(file_id='{self.file_id}', filename='{self.filename}', "
            f"bytes={self.bytes}, provider='{self.provider}', purpose={self.purpose})"
        )
