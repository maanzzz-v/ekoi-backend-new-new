"""Main FastAPI application for the Resume Indexer."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from core.database import db_manager
from core.vector_db import vector_manager
from controllers import resume_router, health_router, chat_router, jd_router, agent_parameters_router
from exceptions.custom_exceptions import ResumeIndexerException
from services.resume_service import resume_service
from utils.logger import configure_application_logging, get_logger

# Configure application-wide logging with colors
configure_application_logging(
    level=settings.log_level.upper(),
    include_colors=True,
    log_file=None,  # Can be configured to log to file if needed
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting Resume Indexer application")

    try:
        # Initialize database connection
        await db_manager.connect()

        # Initialize vector database
        await vector_manager.initialize()

        # Set vector manager dependency in resume service
        resume_service.set_vector_manager(vector_manager)

        # Clean up any invalid documents
        await resume_service.cleanup_invalid_documents()

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Resume Indexer application")
    await db_manager.disconnect()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Resume parser and indexer that extracts key information from resumes and stores it in a vector database for efficient retrieval and search",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resume_router)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(jd_router)
app.include_router(agent_parameters_router)


# Global exception handler
@app.exception_handler(ResumeIndexerException)
async def resume_indexer_exception_handler(request, exc: ResumeIndexerException):
    """Handle custom application exceptions."""
    logger.error(f"Application error: {exc.message}")
    return JSONResponse(
        status_code=500, content={"error": exc.message, "details": exc.details}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Resume Indexer API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
