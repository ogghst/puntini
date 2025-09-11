"""Domain models for the backend."""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class Priority(str, Enum):
    """Priority levels for tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    """Status levels for tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Task(BaseEntity):
    """Task model."""

    id: str
    name: str
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM


class Project(BaseModel):
    """Project model."""

    key: str = Field(..., description="Unique project key")
    name: str
    description: Optional[str] = None


class User(BaseModel):
    """User model."""

    user_id: str
    name: str


class Epic(BaseModel):
    """Epic model."""

    key: str
    title: str
    project_key: str


class Issue(BaseModel):
    """Issue model."""

    key: str
    title: str
    status: Literal["open", "in_progress", "done", "blocked"] = "open"
