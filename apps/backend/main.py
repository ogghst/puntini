"""
FastAPI main application for the business improvement project management system.

This module provides the main FastAPI application with basic endpoints
for the Phase 0 scaffolding requirements.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    agent_router,
    graph_router,
    health_router,
    session_router,
    todo_router,
)
from api.session_manager import get_session_manager
from config.config import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    This handles initialization and cleanup of resources when the FastAPI
    application starts and stops.
    """
    # Startup
    logger.info("Starting FastAPI application...")
    config = ConfigManager()
    logger.info(f"Configuration loaded: {config.config}")

    # Initialize session manager
    session_manager = get_session_manager()
    await session_manager.start()
    logger.info("Session manager started")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application...")

    # Stop session manager
    await session_manager.stop()
    logger.info("Session manager stopped")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Business Improvement Project Management API",
        description="API for managing business improvement projects using Agile and PMI methodologies",
        version="0.1.0",
        lifespan=lifespan
    )

    # Add CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(health_router)
    app.include_router(agent_router)
    app.include_router(graph_router)
    app.include_router(todo_router)
    app.include_router(session_router)

    # Add root endpoint
    @app.get("/")
    async def hello_world():
        """
        Hello world endpoint for basic API connectivity testing.
        
        Returns:
            dict: Simple greeting message with API information
        """
        return {
            "message": "Hello World!",
            "api": "Business Improvement Project Management API",
            "version": "0.1.0",
            "status": "running"
        }

    return app


# Create the FastAPI application instance
app = create_app()






if __name__ == "__main__":
    import uvicorn

    # Get configuration
    config = ConfigManager()
    config_data = config.config

    # Run the server
    uvicorn.run(
        "main:app",
        host=config_data.get("api_host", "0.0.0.0"),
        port=config_data.get("api_port", 8000),
        reload=config_data.get("api_reload", True),
        log_level=config_data.get("log_level", "info").lower()
    )
