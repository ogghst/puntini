"""Session-related Pydantic models for the business improvement project management system.

This module contains Pydantic models for session management, including
session data structures, message types, and API request/response models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session status enumeration."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    ERROR = "error"
    CLEANING_UP = "cleaning_up"


class MessageType(str, Enum):
    """Message type enumeration."""

    USER = "user"
    SYSTEM = "system"
    AGENT = "agent"
    ERROR = "error"


class SessionInfo(BaseModel):
    """Session information model."""

    session_id: UUID = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    project_id: UUID | None = Field(None, description="Project context identifier")
    status: SessionStatus = Field(..., description="Current session status")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    is_expired: bool = Field(..., description="Whether the session has expired")
    is_active: bool = Field(..., description="Whether the session is active")
    agent_count: int = Field(..., description="Number of active agents")
    task_count: int = Field(..., description="Number of pending tasks")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Session metadata"
    )


class Message(BaseModel):
    """Message model for session communication."""

    id: str = Field(..., description="Unique message identifier")
    content: Any = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    message_type: MessageType = Field(..., description="Type of message")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Message metadata"
    )


class SessionCreateRequest(BaseModel):
    """Request model for creating a new session."""

    user_id: str = Field(..., description="User identifier")
    project_id: UUID | None = Field(None, description="Optional project context")
    metadata: dict[str, Any] | None = Field(
        None, description="Optional session metadata"
    )


class SessionResponse(BaseModel):
    """Response model for session information."""

    session_id: UUID = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    project_id: UUID | None = Field(None, description="Project context identifier")
    status: str = Field(..., description="Session status")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    last_activity: str = Field(..., description="Last activity timestamp (ISO format)")
    expires_at: str = Field(..., description="Expiration timestamp (ISO format)")
    is_expired: bool = Field(..., description="Whether the session has expired")
    is_active: bool = Field(..., description="Whether the session is active")
    agent_count: int = Field(..., description="Number of active agents")
    task_count: int = Field(..., description="Number of pending tasks")
    metadata: dict[str, Any] = Field(..., description="Session metadata")


class MessageRequest(BaseModel):
    """Request model for sending a message to a session."""

    content: Any = Field(..., description="Message content")
    message_type: MessageType = Field(
        default=MessageType.USER, description="Type of message"
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Optional message metadata"
    )


class MessageResponse(BaseModel):
    """Response model for message information."""

    message_id: str = Field(..., description="Message identifier")
    content: Any = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp (ISO format)")
    message_type: str = Field(..., description="Message type")
    metadata: dict[str, Any] = Field(..., description="Message metadata")


class ProjectContextUpdate(BaseModel):
    """Model for updating project context."""

    context: dict[str, Any] = Field(..., description="Project context data")


class TaskInfo(BaseModel):
    """Model for task information."""

    id: str = Field(..., description="Task identifier")
    title: str = Field(..., description="Task title")
    description: str | None = Field(None, description="Task description")
    status: Literal["pending", "in_progress", "completed", "cancelled"] = Field(
        default="pending", description="Task status"
    )
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        default="medium", description="Task priority"
    )
    created_at: str = Field(..., description="Task creation timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Task metadata")


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""

    sessions: list[SessionResponse] = Field(..., description="List of sessions")
    total_count: int = Field(..., description="Total number of sessions")
    active_count: int = Field(..., description="Number of active sessions")


class SessionStats(BaseModel):
    """Session statistics model."""

    total_sessions: int = Field(..., description="Total number of sessions")
    active_sessions: int = Field(..., description="Number of active sessions")
    expired_sessions: int = Field(..., description="Number of expired sessions")
    error_sessions: int = Field(..., description="Number of sessions in error state")
    max_sessions: int = Field(..., description="Maximum number of sessions allowed")
    average_session_duration: float | None = Field(
        None, description="Average session duration in seconds"
    )
