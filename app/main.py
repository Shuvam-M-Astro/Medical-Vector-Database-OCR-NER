"""
Main FastAPI application for the medical vector database.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .config import settings
from .api import router, setup_middleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Configure logging
    logger.remove()
    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    logger.add(sys.stderr, level=settings.LOG_LEVEL)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="Medical Vector Database with OCR and NER",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Include API routes
    app.include_router(router)
    
    # Mount static files (if any)
    static_dir = Path("static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Health check endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Medical Vector Database API",
            "version": settings.API_VERSION,
            "docs": "/docs"
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Medical Vector Database API on {settings.API_HOST}:{settings.API_PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    ) 