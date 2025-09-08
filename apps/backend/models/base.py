from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Annotated

class BaseEntity(BaseModel):
    """Abstract base class for all domain entities."""
    id: Annotated[UUID, Field(description="Unique identifier for the entity.")] = Field(default_factory=uuid4)
