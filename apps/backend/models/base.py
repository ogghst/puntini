"""Base models for the backend."""

from pydantic import BaseModel, ConfigDict


class BaseEntity(BaseModel):
    """Base entity model."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True,
    )
