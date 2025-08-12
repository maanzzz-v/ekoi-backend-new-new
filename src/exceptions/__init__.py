"""Exceptions package initialization."""

from .custom_exceptions import (
    ResumeIndexerException,
    FileProcessingError,
    VectorStorageError,
    DatabaseError,
    SearchError,
    ValidationError,
    create_http_exception,
)

__all__ = [
    "ResumeIndexerException",
    "FileProcessingError",
    "VectorStorageError",
    "DatabaseError",
    "SearchError",
    "ValidationError",
    "create_http_exception",
]
