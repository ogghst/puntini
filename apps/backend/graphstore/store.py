from abc import ABC, abstractmethod
from typing import Any, Literal

from models.graph import Patch


class GraphStore(ABC):
    """
    Abstract interface for a GraphStore.
    Defines the contract for persistence and querying operations on a graph database.
    """

    @abstractmethod
    def upsert(self, patches: list[Patch]) -> dict[str, Any]:
        """
        Applies a list of idempotent patch operations to the graph.
        
        Args:
            patches: A list of Patch objects (AddNode, UpdateProps, AddEdge, Delete).
            
        Returns:
            A dictionary with the outcome of the operation.
        """
        pass

    @abstractmethod
    def query_graph(self, query: str, engine: Literal["cypher", "ngql"] = "cypher") -> list[dict[str, Any]]:
        """
        Executes a raw query against the graph database.
        
        Args:
            query: The query string (Cypher or nGQL).
            engine: The query engine to use.
            
        Returns:
            A list of result rows, where each row is a dictionary.
        """
        pass

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """
        Checks the health of the connection to the graph database.
        
        Returns:
            A dictionary containing health status information.
        """
        pass
