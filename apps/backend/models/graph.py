"""Graph-related models for the backend."""

from typing import Dict, Literal, Optional

from pydantic import BaseModel


class NodeSpec(BaseModel):
    """Node specification for patches."""

    label: Literal["Project", "User", "Epic", "Issue", "ASSIGNMENT"]
    key: str
    props: Dict = {}


class EdgeSpec(BaseModel):
    """Edge specification for patches."""

    src_label: Literal["Project", "Epic", "Issue", "ASSIGNMENT"]
    src_key: str
    rel: Literal[
        "HAS_EPIC", "HAS_ISSUE", "ASSIGNED_TO", "BLOCKS", "HAS_ASSIGNMENT", "ASSIGNMENT_OF"
    ]
    dst_label: Literal["Epic", "Issue", "User", "ASSIGNMENT"]
    dst_key: str
    props: Dict = {}


class Patch(BaseModel):
    """Patch model for graph operations."""

    op: Literal["AddNode", "UpdateProps", "AddEdge", "Delete"]
    node: Optional[NodeSpec] = None
    edge: Optional[EdgeSpec] = None
