"""Resume upload and processing API endpoints."""

import logging
import time
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from models.schemas import UploadResponse, SearchRequest, SearchResponse
from services.resume_service import resume_service
from exceptions.custom_exceptions import (
    FileProcessingError,
    VectorStorageError,
    DatabaseError,
    create_http_exception,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


@router.post("/upload", response_model=UploadResponse)
async def upload_resumes(
    files: List[UploadFile] = File(..., description="Resume files to upload"),
):
    """
    Upload multiple resume files for processing and indexing.

    Supported file types: PDF, DOCX, TXT
    Maximum file size: 10MB per file
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        logger.info(f"Processing {len(files)} uploaded files")

        # Process the files
        results = await resume_service.process_uploaded_files(files)

        # Prepare response
        uploaded_files = [item["filename"] for item in results["processed_files"]]

        response = UploadResponse(
            message=f"Successfully processed {results['success_count']} out of {results['total_files']} files",
            uploaded_files=uploaded_files,
            total_files=results["total_files"],
            success=results["error_count"] == 0,
        )

        # If there were any failures, include them in the response
        if results["failed_files"]:
            response.message += f". {results['error_count']} files failed to process."
            # You might want to add failed_files to the response model

        status_code = 200 if results["success_count"] > 0 else 400

        return JSONResponse(status_code=status_code, content=response.dict())

    except FileProcessingError as e:
        logger.error(f"File processing error: {e}")
        raise create_http_exception(400, str(e), e.details)

    except VectorStorageError as e:
        logger.error(f"Vector storage error: {e}")
        raise create_http_exception(500, str(e), e.details)

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise create_http_exception(500, str(e), e.details)

    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise create_http_exception(
            500, "Internal server error occurred during file processing"
        )


@router.post("/search", response_model=SearchResponse)
async def search_resumes(request: SearchRequest):
    """
    Search for resumes based on requirements and keywords.

    Uses vector similarity search to find resumes that best match
    the provided query and requirements.
    """
    try:
        start_time = time.time()

        logger.info(f"Searching resumes with query: {request.query}")

        # Perform search
        matches = await resume_service.search_resumes(
            query=request.query, top_k=request.top_k, filters=request.filters
        )

        processing_time = time.time() - start_time

        response = SearchResponse(
            query=request.query,
            total_results=len(matches),
            matches=matches,
            processing_time=round(processing_time, 3),
            success=True,
        )

        logger.info(f"Found {len(matches)} matches in {processing_time:.3f}s")

        return response

    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise create_http_exception(500, "Error occurred during search")


@router.get("/")
async def list_resumes(
    skip: int = Query(0, ge=0, description="Number of resumes to skip"),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of resumes to return"
    ),
):
    """
    List all uploaded resumes with pagination.
    """
    try:
        resumes = await resume_service.get_all_resumes(skip=skip, limit=limit)

        return {"resumes": resumes, "total": len(resumes), "skip": skip, "limit": limit}

    except Exception as e:
        logger.error(f"Error listing resumes: {e}")
        raise create_http_exception(500, "Error occurred while listing resumes")


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    """
    Get detailed information about a specific resume.
    """
    try:
        resume = await resume_service.get_resume_by_id(resume_id)

        if not resume:
            raise create_http_exception(404, "Resume not found")

        return resume

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving resume {resume_id}: {e}")
        raise create_http_exception(500, "Error occurred while retrieving resume")


@router.delete("/{resume_id}")
async def delete_resume(resume_id: str):
    """
    Delete a resume and its associated vectors.
    """
    try:
        success = await resume_service.delete_resume(resume_id)

        if not success:
            raise create_http_exception(404, "Resume not found or could not be deleted")

        return {"message": "Resume deleted successfully", "resume_id": resume_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {e}")
        raise create_http_exception(500, "Error occurred while deleting resume")
