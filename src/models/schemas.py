"""Data models and schemas for the resume indexer."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ResumeMetadata(BaseModel):
    """Resume metadata model for MongoDB storage."""

    id: Optional[str] = Field(default=None, alias="_id")
    file_name: str
    file_type: str
    file_size: int
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    processing_timestamp: Optional[datetime] = None
    vector_ids: Optional[List[str]] = None  # Pinecone vector IDs

    # Extracted information
    extracted_text: Optional[str] = None
    parsed_info: Optional[Dict[str, Any]] = None

    def dict(self, **kwargs):
        """Override dict method to exclude None _id values."""
        data = super().dict(**kwargs)
        # Remove _id if it's None to prevent MongoDB issues
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        return data

    class Config:
        """Pydantic config."""

        populate_by_name = True
        arbitrary_types_allowed = True


class ExtractedInfo(BaseModel):
    """Structured information extracted from resume."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None


class UploadResponse(BaseModel):
    """Response model for file upload."""

    message: str
    uploaded_files: List[str]
    total_files: int
    success: bool = True


class SearchRequest(BaseModel):
    """Request model for resume search."""

    query: str = Field(..., description="Search query describing requirements")
    top_k: int = Field(default=10, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional filters"
    )


class ResumeMatch(BaseModel):
    """Resume search result model."""

    id: str
    file_name: str
    score: float
    extracted_info: Optional[ExtractedInfo] = None
    relevant_text: Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for resume search."""

    query: str
    total_results: int
    matches: List[ResumeMatch]
    processing_time: float
    success: bool = True


class ChatRequest(BaseModel):
    """Request model for chat-based resume search."""

    message: str = Field(..., description="Natural language search message")
    top_k: int = Field(default=10, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional filters"
    )


class ChatResponse(BaseModel):
    """Response model for chat-based resume search."""

    message: str = Field(..., description="Conversational response")
    query: str = Field(..., description="Processed search query")
    original_message: str = Field(..., description="Original user message")
    matches: List[ResumeMatch]
    total_results: int
    success: bool = True
