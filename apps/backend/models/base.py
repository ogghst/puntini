from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """Abstract base class for all domain entities."""
    id: Annotated[UUID, Field(description="Unique identifier for the entity.")] = Field(default_factory=uuid4)
