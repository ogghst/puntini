"""Models package for the business improvement project management system.

This package contains all Pydantic models used throughout the application,
including domain entities, graph operations, and session management.
"""

from .base import BaseEntity
from .domain import Epic, Issue, Project, User
from .graph import EdgeSpec, NodeSpec, Patch
from .session import (
    Message,
    MessageRequest,
    MessageResponse,
    MessageType,
    ProjectContextUpdate,
    SessionCreateRequest,
    SessionInfo,
    SessionListResponse,
    SessionResponse,
    SessionStats,
    SessionStatus,
    TaskInfo,
)

__all__ = [
    "BaseEntity",
    "EdgeSpec",
    "Epic",
    "Issue",
    "Message",
    "MessageRequest",
    "MessageResponse",
    "MessageType",
    "NodeSpec",
    "Patch",
    "Project",
    "ProjectContextUpdate",
    "SessionCreateRequest",
    "SessionInfo",
    "SessionListResponse",
    "SessionResponse",
    "SessionStats",
    "SessionStatus",
    "TaskInfo",
    "User",
]
