"""
In-memory GraphStore implementation using NetworkX.
"""

import logging
from typing import Any, Dict, List, Literal

import networkx as nx
from models.graph import EdgeSpec, Patch
from graphstore.store import GraphStore


class NetworkXGraphStore(GraphStore):
    """NetworkX implementation of GraphStore interface"""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized NetworkXGraphStore")

    def upsert(self, patches: List[Patch]) -> Dict[str, Any]:
        """
        Apply patches to the in-memory graph.

        Args:
            patches: List of graph operations to apply.

        Returns:
            OperationResult with success status and details.
        """
        if not patches:
            return {"success": True, "message": "No patches to apply", "applied": 0}

        applied_count = 0
        errors = []

        for patch in patches:
            try:
                if patch.op == "AddNode" and patch.node:
                    node_id = f"{patch.node.label}:{patch.node.key}"
                    if not self.graph.has_node(node_id):
                        self.graph.add_node(
                            node_id,
                            label=patch.node.label,
                            key=patch.node.key,
                            **patch.node.props,
                        )
                        applied_count += 1
                elif patch.op == "UpdateProps" and patch.node:
                    node_id = f"{patch.node.label}:{patch.node.key}"
                    if self.graph.has_node(node_id):
                        self.graph.nodes[node_id].update(patch.node.props)
                        applied_count += 1
                elif patch.op == "AddEdge" and patch.edge:
                    src_id = f"{patch.edge.src_label}:{patch.edge.src_key}"
                    dst_id = f"{patch.edge.dst_label}:{patch.edge.dst_key}"
                    if self.graph.has_node(src_id) and self.graph.has_node(dst_id):
                        self.graph.add_edge(
                            src_id, dst_id, key=patch.edge.rel, **patch.edge.props
                        )
                        applied_count += 1
                elif patch.op == "Delete":
                    if patch.node:
                        node_id = f"{patch.node.label}:{patch.node.key}"
                        if self.graph.has_node(node_id):
                            self.graph.remove_node(node_id)
                            applied_count += 1
                    elif patch.edge:
                        src_id = f"{patch.edge.src_label}:{patch.edge.src_key}"
                        dst_id = f"{patch.edge.dst_label}:{patch.edge.dst_key}"
                        if self.graph.has_edge(src_id, dst_id, key=patch.edge.rel):
                            self.graph.remove_edge(src_id, dst_id, key=patch.edge.rel)
                            applied_count += 1
            except Exception as e:
                error_msg = f"Failed to apply patch {patch.op}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        if errors:
            return {
                "success": False,
                "message": f"Encountered {len(errors)} errors",
                "errors": errors,
                "applied": applied_count,
            }

        return {
            "success": True,
            "message": f"Successfully applied {applied_count} patches",
            "applied": applied_count,
            "errors": [],
        }

    def query_graph(
        self, query: str, engine: Literal["cypher", "ngql"] = "cypher"
    ) -> List[Dict[str, Any]]:
        """
        NetworkX does not support Cypher or nGQL. This method is a no-op.
        """
        self.logger.warning(
            f"query_graph is not implemented for NetworkXGraphStore. Query: {query}"
        )
        return []

    def health(self) -> Dict[str, Any]:
        """
        Check the health of the in-memory graph store.
        """
        return {
            "status": "healthy",
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
        }
