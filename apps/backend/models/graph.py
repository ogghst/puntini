"""Graph-related models for the backend."""

from typing import Any, Literal

from .base import BaseEntity


class Node(BaseEntity):
    """Node model."""

    id: str
    type: str
    properties: dict[str, Any]


class Edge(BaseEntity):
    """Edge model."""

    source: str
    target: str
    type: str
    properties: dict[str, Any] | None = None


class Patch(BaseEntity):
    """Patch model."""

    op: Literal["add", "update", "delete"]
    entity: Literal["node", "edge"]
    data: dict[str, Any]
