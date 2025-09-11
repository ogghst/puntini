from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class Project(BaseEntity):
    """Represents a project."""
    name: Annotated[str, Field(description="The name of the project.")]
    description: Annotated[str | None, Field(description="A brief description of the project.")] = None

class User(BaseEntity):
    """Represents a user."""
    user_id: Annotated[str, Field(description="The user's unique ID from an external system.")]
    name: Annotated[str, Field(description="The user's full name.")]

class Epic(BaseEntity):
    """Represents an epic within a project."""
    title: Annotated[str, Field(description="The title of the epic.")]
    project_id: Annotated[UUID, Field(description="The ID of the project this epic belongs to.")]

class Issue(BaseEntity):
    """Represents an issue within an epic."""
    title: Annotated[str, Field(description="The title of the issue.")]
    status: Annotated[Literal["open","in_progress","done","blocked"], Field(description="The current status of the issue.")] = "open"
