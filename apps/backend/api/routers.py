"""
API routers for the FastAPI application.

This module contains all API router definitions that will be used
to organize endpoints by functionality.
"""

from fastapi import APIRouter

# Create router instances for different functional areas
health_router = APIRouter(prefix="/health", tags=["health"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])
graph_router = APIRouter(prefix="/graph", tags=["graph"])
todo_router = APIRouter(prefix="/todo", tags=["todo"])


@health_router.get("/")
async def health_status():
    """
    Detailed health status endpoint.
    
    Returns:
        dict: Detailed health information
    """
    return {
        "status": "healthy",
        "service": "business-improvement-api",
        "version": "0.1.0",
        "components": {
            "api": "operational",
            "database": "not_configured",  # Will be updated when graph stores are implemented
            "agent": "not_configured"      # Will be updated when LangGraph is implemented
        }
    }


@agent_router.post("/act")
async def agent_action():
    """
    Placeholder for agent action endpoint.
    
    This will be implemented in Phase 1 for the Extract→Validate→Upsert→Answer flow.
    """
    return {
        "message": "Agent action endpoint - to be implemented in Phase 1",
        "status": "placeholder"
    }


@graph_router.post("/patch")
async def graph_patch():
    """
    Placeholder for graph patch endpoint.
    
    This will be implemented in Phase 1 for graph modifications.
    """
    return {
        "message": "Graph patch endpoint - to be implemented in Phase 1",
        "status": "placeholder"
    }


@graph_router.get("/query")
async def graph_query():
    """
    Placeholder for graph query endpoint.
    
    This will be implemented in Phase 1 for graph queries.
    """
    return {
        "message": "Graph query endpoint - to be implemented in Phase 1",
        "status": "placeholder"
    }


@todo_router.get("/")
async def get_todos():
    """
    Placeholder for TODO list endpoint.
    
    This will be implemented in Phase 1 for TODO management.
    """
    return {
        "message": "TODO list endpoint - to be implemented in Phase 1",
        "status": "placeholder"
    }


@todo_router.post("/")
async def create_todo():
    """
    Placeholder for TODO creation endpoint.
    
    This will be implemented in Phase 1 for TODO management.
    """
    return {
        "message": "TODO creation endpoint - to be implemented in Phase 1",
        "status": "placeholder"
    }
