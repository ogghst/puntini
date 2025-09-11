"""
API routers for the FastAPI application.

This module contains all API router definitions that will be used
to organize endpoints by functionality.
"""

import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from models.session import (
    MessageRequest,
    MessageResponse,
    SessionCreateRequest,
    SessionListResponse,
    SessionResponse,
    SessionStats,
)
from api.session_manager import SessionManager, SessionNotFoundError, get_session_manager

# Create router instances for different functional areas
health_router = APIRouter(prefix="/health", tags=["health"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])
graph_router = APIRouter(prefix="/graph", tags=["graph"])
todo_router = APIRouter(prefix="/todo", tags=["todo"])
session_router = APIRouter(prefix="/sessions", tags=["sessions"], redirect_slashes=False)

# Simple rate limiting for session creation
_session_creation_times = {}


def reset_rate_limiting():
    """Reset rate limiting state for testing."""
    global _session_creation_times
    _session_creation_times.clear()


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


# Session Management Endpoints

def get_session_manager_dependency() -> SessionManager:
    """Dependency to get the session manager instance."""
    return get_session_manager()


@session_router.post("", response_model=SessionResponse)
@session_router.post("/", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Create a new user session.
    
    Creates a new session with the specified user and optional project context.
    The session will be automatically initialized with available agents.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Simple rate limiting - prevent creation of multiple sessions within 1 second
    current_time = time.time()
    user_key = f"{request.user_id}_{request.project_id}"
    
    if user_key in _session_creation_times:
        time_since_last = current_time - _session_creation_times[user_key]
        if time_since_last < 1.0:  # 1 second cooldown
            logger.warning(f"Rate limiting session creation for user {request.user_id} - too frequent")
            raise HTTPException(
                status_code=429, 
                detail="Session creation rate limited. Please wait before creating another session."
            )
    
    _session_creation_times[user_key] = current_time
    
    try:
        logger.info(f"Creating session for user: {request.user_id}, project: {request.project_id}")
        session = await session_manager.create_session(
            user_id=request.user_id,
            project_id=request.project_id,
            metadata=request.metadata
        )
        session_info = session.session_info
        logger.info(f"Session created successfully: {session_info.session_id}")
        return SessionResponse(
            session_id=session_info.session_id,
            user_id=session_info.user_id,
            project_id=session_info.project_id,
            status=session_info.status.value,
            created_at=session_info.created_at.isoformat(),
            last_activity=session_info.last_activity.isoformat(),
            expires_at=session_info.expires_at.isoformat(),
            is_expired=session_info.is_expired,
            is_active=session_info.is_active,
            agent_count=session_info.agent_count,
            task_count=session_info.task_count,
            metadata=session_info.metadata
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e!s}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {e!s}") from e


@session_router.get("/stats", response_model=SessionStats)
async def get_session_stats(
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Get session statistics.
    
    Retrieves comprehensive statistics about all sessions.
    """
    try:
        sessions = await session_manager.list_sessions()
        total_sessions = len(sessions)
        active_sessions = sum(1 for s in sessions if s.is_active())
        expired_sessions = sum(1 for s in sessions if s.is_expired())
        error_sessions = sum(1 for s in sessions if s.status.value == "error")

        # Calculate average session duration for completed sessions
        completed_sessions = [s for s in sessions if s.status.value in ["expired", "cleaning_up"]]
        if completed_sessions:
            durations = [(s.last_activity - s.created_at).total_seconds() for s in completed_sessions]
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = None

        return SessionStats(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            expired_sessions=expired_sessions,
            error_sessions=error_sessions,
            max_sessions=session_manager.max_sessions,
            average_session_duration=avg_duration
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {e!s}") from e


@session_router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Get session information.
    
    Retrieves detailed information about a specific session including
    status, activity, and resource counts.
    """
    try:
        session = await session_manager.get_session(session_id)
        session_info = session.session_info
        return SessionResponse(
            session_id=session_info.session_id,
            user_id=session_info.user_id,
            project_id=session_info.project_id,
            status=session_info.status.value,
            created_at=session_info.created_at.isoformat(),
            last_activity=session_info.last_activity.isoformat(),
            expires_at=session_info.expires_at.isoformat(),
            is_expired=session_info.is_expired,
            is_active=session_info.is_active,
            agent_count=session_info.agent_count,
            task_count=session_info.task_count,
            metadata=session_info.metadata
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {e!s}") from e


@session_router.delete("/{session_id}")
async def destroy_session(
    session_id: UUID,
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Destroy a session.
    
    Permanently destroys the session and cleans up all associated resources.
    """
    try:
        success = await session_manager.destroy_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session destroyed successfully"}
    except HTTPException:
        # Re-raise HTTPException to let FastAPI handle it
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to destroy session: {e!s}") from e


@session_router.get("", response_model=SessionListResponse)
@session_router.get("/", response_model=SessionListResponse)
async def list_sessions(
    user_id: str | None = None,
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    List active sessions.
    
    Lists all active sessions, optionally filtered by user ID.
    """
    try:
        sessions = await session_manager.list_sessions(user_id=user_id)
        session_responses = []
        for session in sessions:
            session_info = session.session_info
            session_responses.append(SessionResponse(
                session_id=session_info.session_id,
                user_id=session_info.user_id,
                project_id=session_info.project_id,
                status=session_info.status.value,
                created_at=session_info.created_at.isoformat(),
                last_activity=session_info.last_activity.isoformat(),
                expires_at=session_info.expires_at.isoformat(),
                is_expired=session_info.is_expired,
                is_active=session_info.is_active,
                agent_count=session_info.agent_count,
                task_count=session_info.task_count,
                metadata=session_info.metadata
            ))
        active_count = sum(1 for s in session_responses if s.is_active)

        return SessionListResponse(
            sessions=session_responses,
            total_count=len(session_responses),
            active_count=active_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {e!s}") from e


@session_router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: UUID,
    request: MessageRequest,
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Send a message to a session.
    
    Sends a message to the specified session for processing by agents.
    """
    try:
        session = await session_manager.get_session(session_id)
        message_id = await session.send_message(
            content=request.content,
            message_type=request.message_type,
            metadata=request.metadata
        )

        # Get the message details for response
        return MessageResponse(
            message_id=message_id,
            content=request.content,
            timestamp=session.last_activity.isoformat(),
            message_type=request.message_type,
            metadata=request.metadata or {}
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e!s}") from e


@session_router.get("/{session_id}/messages")
async def receive_messages(
    session_id: UUID,
    timeout: float | None = None,
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Receive messages from a session.
    
    Retrieves messages from the session's output queue.
    """
    try:
        session = await session_manager.get_session(session_id)
        message = await session.receive_message(timeout=timeout)

        if message is None:
            return {"message": "No messages available", "timeout": True}

        return MessageResponse(
            message_id=message.id,
            content=message.content,
            timestamp=message.timestamp.isoformat(),
            message_type=message.message_type,
            metadata=message.metadata
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to receive message: {e!s}") from e


@session_router.get("/{session_id}/context")
async def get_project_context(
    session_id: UUID,
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Get project context for a session.
    
    Retrieves the current project context and task information.
    """
    try:
        session = await session_manager.get_session(session_id)
        context = await session.get_project_context()
        tasks = await session.get_tasks()

        return {
            "project_context": context,
            "tasks": tasks,
            "task_count": len(tasks)
        }
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {e!s}") from e


@session_router.put("/{session_id}/context")
async def update_project_context(
    session_id: UUID,
    context: dict[str, Any],
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Update project context for a session.
    
    Updates the project context with new information.
    """
    try:
        session = await session_manager.get_session(session_id)
        await session.update_project_context(context)
        return {"message": "Project context updated successfully"}
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update context: {e!s}") from e


@session_router.post("/{session_id}/tasks")
async def add_task(
    session_id: UUID,
    task: dict[str, Any],
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Add a task to a session.
    
    Adds a new task to the session's task queue.
    """
    try:
        session = await session_manager.get_session(session_id)
        await session.add_task(task)
        return {"message": "Task added successfully"}
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add task: {e!s}") from e


@session_router.get("/{session_id}/tasks")
async def get_tasks(
    session_id: UUID,
    session_manager: SessionManager = Depends(get_session_manager_dependency)
):
    """
    Get tasks for a session.
    
    Retrieves all tasks associated with the session.
    """
    try:
        session = await session_manager.get_session(session_id)
        tasks = await session.get_tasks()
        return {"tasks": tasks, "count": len(tasks)}
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {e!s}") from e
