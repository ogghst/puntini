from typing import Annotated, Literal

from pydantic import BaseModel, Field
from models.base import BaseEntity

class NodeSpec(BaseEntity):
    """Specification for a node in the graph."""
    label: Annotated[Literal["Project","User","Epic","Issue","Assignment"], Field(description="The label of the node.")]
    #key: Annotated[str, Field(description="The unique key of the node.")]
    props: Annotated[dict, Field(description="A dictionary of properties for the node.")] = {}

class EdgeSpec(BaseEntity):
    """Specification for an edge in the graph."""
    src_label: Annotated[Literal["Project","User""Epic","Issue","Assignment"], Field(description="The label of the source node.")]
    src_id: Annotated[str, Field(description="The unique key of the source node.")]
    rel: Annotated[Literal["HAS_EPIC","HAS_ISSUE","ASSIGNED_TO","BLOCKS","HAS_ASSIGNMENT","ASSIGNMENT_OF"], Field(description="The type of the relationship.")]
    dst_label: Annotated[Literal["Project","Epic","Issue","User","Assignment"], Field(description="The label of the destination node.")]
    dst_id: Annotated[str, Field(description="The unique key of the destination node.")]
    props: Annotated[dict, Field(description="A dictionary of properties for the edge.")] = {}

class Patch(BaseEntity):
    """Represents a single operation to be applied to the graph."""
    op: Annotated[Literal["AddNode","UpdateProps","AddEdge","Delete"], Field(description="The operation to perform.")]
    node: Annotated[NodeSpec | None, Field(description="The node specification for the operation.")] = None
    edge: Annotated[EdgeSpec | None, Field(description="The edge specification for the operation.")] = None
    reason: Annotated[str, Field(description="The reason for the operation.")] = ""