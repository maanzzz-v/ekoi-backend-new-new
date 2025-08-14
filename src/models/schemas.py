"""Data models and schemas for the resume indexer."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field



class MessageType(str, Enum):
    """Types of messages in a chat session."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual message in a chat session."""
    id: str = Field(..., description="Unique message ID")
    type: MessageType = Field(..., description="Type of message")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")


class ChatSession(BaseModel):
    """Chat session for resume search conversations."""
    id: str = Field(..., description="Unique session ID")
    title: str = Field(..., description="Session title/summary")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[ChatMessage] = Field(default_factory=list)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Session context and state")
    is_active: bool = Field(default=True)


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""
    title: Optional[str] = Field(default=None, description="Optional session title")
    initial_message: Optional[str] = Field(default=None, description="Optional initial message")


class AddMessageRequest(BaseModel):
    """Request to add a message to an existing session."""
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="User message content")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class SessionResponse(BaseModel):
    """Response containing session information."""
    session: ChatSession
    success: bool = True
    message: str = "Session operation successful"


class SessionListResponse(BaseModel):
    """Response containing list of sessions."""
    sessions: List[ChatSession]
    total: int
    success: bool = True


class FollowUpRequest(BaseModel):
    """Request for follow-up questions about search results."""
    question: str = Field(..., description="Follow-up question")
    previous_search_results: Optional[List[str]] = Field(default=None, description="IDs of previously found resumes")

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ResumeMetadata(BaseModel):
    """Resume metadata model for MongoDB storage."""

    id: Optional[str] = Field(default=None, alias="_id")
    file_name: str
    file_type: str
    file_size: int
    file_path: Optional[str] = None  # Path to the stored file
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
    """Enhanced response model for chat-based resume search with UI optimization."""

    message: str = Field(..., description="Conversational response")
    query: str = Field(..., description="Processed search query")
    original_message: str = Field(..., description="Original user message")
    matches: List[ResumeMatch]
    total_results: int
    success: bool = True
    session_id: Optional[str] = Field(default=None, description="Session ID if search was performed in a session")
    
    # UI Optimization fields
    ui_components: Optional[Dict[str, Any]] = Field(default=None, description="Structured UI components for frontend")
    conversation_flow: Optional[Dict[str, Any]] = Field(default=None, description="Conversation flow suggestions")
    quick_actions: Optional[List[Dict[str, str]]] = Field(default=None, description="Quick action buttons for UI")
    response_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response optimization metadata")


class OptimizedFollowUpResponse(BaseModel):
    """Enhanced response model for follow-up questions with UI optimization."""
    
    session_id: str
    question: str
    answer: str
    ui_components: Optional[Dict[str, Any]] = Field(default=None, description="UI components for display")
    conversation_flow: Optional[Dict[str, Any]] = Field(default=None, description="Next conversation suggestions")
    quick_actions: Optional[List[Dict[str, str]]] = Field(default=None, description="Quick actions for follow-up")
    response_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")
    success: bool = True


class AgentParameter(BaseModel):
    """Schema for agent parameters."""
    agent_name: str = Field(..., description="Name of the agent")
    parameter1: int = Field(..., description="Weight for parameter 1")
    parameter2: int = Field(..., description="Weight for parameter 2")
    parameter3: int = Field(..., description="Weight for parameter 3")
    parameter4: int = Field(..., description="Weight for parameter 4")
