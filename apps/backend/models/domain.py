from typing import Optional, Literal, Annotated
from uuid import UUID
from pydantic import Field
from .base import BaseEntity

class Progetto(BaseEntity):
    """Represents a project."""
    nome: Annotated[str, Field(description="The name of the project.")]
    descrizione: Annotated[Optional[str], Field(description="A brief description of the project.")] = None

class Utente(BaseEntity):
    """Represents a user."""
    user_id: Annotated[str, Field(description="The user's unique ID from an external system.")]
    nome: Annotated[str, Field(description="The user's full name.")]

class Epic(BaseEntity):
    """Represents an epic within a project."""
    titolo: Annotated[str, Field(description="The title of the epic.")]
    progetto_id: Annotated[UUID, Field(description="The ID of the project this epic belongs to.")]

class Issue(BaseEntity):
    """Represents an issue within an epic."""
    titolo: Annotated[str, Field(description="The title of the issue.")]
    stato: Annotated[Literal["open","in_progress","done","blocked"], Field(description="The current status of the issue.")] = "open"
