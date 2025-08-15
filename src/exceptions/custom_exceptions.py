"""Custom exception classes for the resume indexer."""

from fastapi import HTTPException
from typing import Any, Dict, Optional


class ResumeIndexerException(Exception):
    """Base exception for resume indexer."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileProcessingError(ResumeIndexerException):
    """Exception raised when file processing fails."""

    pass


class VectorStorageError(ResumeIndexerException):
    """Exception raised when vector storage operations fail."""

    pass


class DatabaseError(ResumeIndexerException):
    """Exception raised when database operations fail."""

    pass


class SearchError(ResumeIndexerException):
    """Exception raised when search operations fail."""

    pass


class ValidationError(ResumeIndexerException):
    """Exception raised when validation fails."""

    pass


# HTTP Exception helpers
def create_http_exception(
    status_code: int, message: str, details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create HTTP exception with details."""
    return HTTPException(
        status_code=status_code, detail={"error": message, "details": details or {}}
    )
