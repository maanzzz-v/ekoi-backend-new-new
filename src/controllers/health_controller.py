"""Health check and system status endpoints."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config.settings import settings
from core.database import db_manager
from core.vector_db import vector_manager
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check including dependencies."""
    status = {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "components": {},
    }

    overall_healthy = True

    # Check database connection
    try:
        if db_manager.database is not None:
            await db_manager.client.admin.command("ismaster")
            status["components"]["database"] = {"status": "healthy", "type": "MongoDB"}
        else:
            status["components"]["database"] = {
                "status": "disconnected",
                "type": "MongoDB",
            }
            overall_healthy = False
    except Exception as e:
        status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # Check vector database
    try:
        if vector_manager.faiss_index or vector_manager.pinecone_index:
            status["components"]["vector_db"] = {
                "status": "healthy",
                "llm_provider": llm_service.get_provider_info(),
                "pinecone_available": vector_manager.pinecone_index is not None,
                "faiss_available": vector_manager.faiss_index is not None,
            }
        else:
            status["components"]["vector_db"] = {"status": "not_initialized"}
            overall_healthy = False
    except Exception as e:
        status["components"]["vector_db"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    if not overall_healthy:
        status["status"] = "unhealthy"
        return JSONResponse(status_code=503, content=status)

    return status


@router.get("/llm-provider")
async def get_llm_provider_info():
    """Get information about the current LLM provider."""
    try:
        provider_info = llm_service.get_provider_info()
        return {
            "status": "success",
            "provider_info": provider_info,
            "available_providers": [
                "sentence-transformers",
                "openai",
                "gemini",
                "ollama",
                "vllm",
            ],
        }
    except Exception as e:
        logger.error(f"Error getting LLM provider info: {e}")
        return JSONResponse(
            status_code=500, content={"error": "Failed to get LLM provider information"}
        )
