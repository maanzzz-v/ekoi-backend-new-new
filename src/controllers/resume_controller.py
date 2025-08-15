"""Resume upload and processing API endpoints."""

import time
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse

from models.schemas import UploadResponse, SearchRequest, SearchResponse
from services.resume_service import resume_service
from exceptions.custom_exceptions import (
    FileProcessingError,
    VectorStorageError,
    DatabaseError,
    create_http_exception,
)
from utils.logger import get_logger

logger = get_logger(__name__)

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
    List all uploaded resumes with pagination and detailed information.
    
    Returns comprehensive information about each uploaded resume including:
    - File details (name, type, size, upload time)
    - Processing status
    - Extracted information (name, email, skills, etc.)
    - File path for access
    """
    try:
        resumes = await resume_service.get_all_resumes(skip=skip, limit=limit)
        
        # Get total count for better pagination info
        total_count = await resume_service.get_total_resume_count()
        
        # Format the response with more useful information
        formatted_resumes = []
        for resume in resumes:
            # Safely handle vector_ids which might be None
            vector_ids = resume.get("vector_ids", [])
            if vector_ids is None:
                vector_ids = []
            
            formatted_resume = {
                "id": str(resume.get("_id", "")),
                "file_name": resume.get("file_name", ""),
                "file_type": resume.get("file_type", ""),
                "file_size": resume.get("file_size", 0),
                "file_path": resume.get("file_path", ""),
                "upload_timestamp": resume.get("upload_timestamp"),
                "processed": resume.get("processed", False),
                "processing_timestamp": resume.get("processing_timestamp"),
                "extracted_info": resume.get("parsed_info", {}),
                "has_vectors": bool(vector_ids),
                "vector_count": len(vector_ids),
            }
            formatted_resumes.append(formatted_resume)

        return {
            "resumes": formatted_resumes,
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "current_page": (skip // limit) + 1,
                "total_pages": (total_count + limit - 1) // limit,
                "has_next": skip + limit < total_count,
                "has_previous": skip > 0,
            },
            "summary": {
                "total_resumes": total_count,
                "showing": len(formatted_resumes),
                "processed": sum(1 for r in formatted_resumes if r["processed"]),
                "unprocessed": sum(1 for r in formatted_resumes if not r["processed"]),
            }
        }

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


@router.get("/{resume_id}/download")
async def download_resume(resume_id: str):
    """
    Download the original resume file.
    """
    try:
        import os
        
        resume = await resume_service.get_resume_by_id(resume_id)

        if not resume:
            raise create_http_exception(404, "Resume not found")

        file_path = resume.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise create_http_exception(404, "Resume file not found on disk")

        # Return the file for download
        filename = resume.get("file_name", "resume")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resume {resume_id}: {e}")
        raise create_http_exception(500, "Error occurred while downloading resume")
