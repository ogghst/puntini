"""
Neo4j GraphStore implementation with Patch→Cypher mapping.
Provides idempotent operations and constraint validation.
"""

import logging
from typing import Any, Dict, List, Literal, Optional
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, TransientError
from models.graph import Patch, NodeSpec, EdgeSpec
from graphstore.store import GraphStore


class Neo4jStore(GraphStore):
    """Neo4j implementation of GraphStore interface"""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver: Optional[Driver] = None
        self.logger = logging.getLogger(__name__)
        self._initialize_constraints()
    
    def _get_driver(self) -> Driver:
        """Get Neo4j driver instance"""
        if self.driver is None:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
        return self.driver
    
    def _initialize_constraints(self):
        """Initialize Neo4j constraints for data integrity"""
        constraints = [
            # Node constraints
            "CREATE CONSTRAINT proj_key_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.key IS UNIQUE",
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            "CREATE CONSTRAINT epic_key_unique IF NOT EXISTS FOR (e:Epic) REQUIRE e.key IS UNIQUE",
            "CREATE CONSTRAINT issue_key_unique IF NOT EXISTS FOR (i:Issue) REQUIRE i.key IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX proj_name_idx IF NOT EXISTS FOR (p:Project) ON (p.nome)",
            "CREATE INDEX user_name_idx IF NOT EXISTS FOR (u:User) ON (u.nome)",
            "CREATE INDEX epic_title_idx IF NOT EXISTS FOR (e:Epic) ON (e.titolo)",
            "CREATE INDEX issue_title_idx IF NOT EXISTS FOR (i:Issue) ON (i.titolo)",
            "CREATE INDEX issue_status_idx IF NOT EXISTS FOR (i:Issue) ON (i.stato)",
        ]
        
        try:
            with self._get_driver().session(database=self.database) as session:
                for constraint in constraints:
                    try:
                        session.run(constraint)
                        self.logger.debug(f"Applied constraint: {constraint}")
                    except Exception as e:
                        self.logger.warning(f"Constraint may already exist: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize constraints: {e}")
    
    def upsert(self, patches: List[Patch]) -> Dict[str, Any]:
        """
        Apply patches atomically with rollback on failure
        
        Args:
            patches: List of graph operations to apply
            
        Returns:
            OperationResult with success status and details
        """
        if not patches:
            return {"success": True, "message": "No patches to apply", "applied": 0}
        
        try:
            with self._get_driver().session(database=self.database) as session:
                with session.begin_transaction() as tx:
                    applied_count = 0
                    errors = []
                    
                    for patch in patches:
                        try:
                            cypher_query = self._patch_to_cypher(patch)
                            result = tx.run(cypher_query)
                            
                            # Check if operation was successful
                            summary = result.consume()
                            if summary.counters.nodes_created > 0 or summary.counters.relationships_created > 0:
                                applied_count += 1
                                self.logger.debug(f"Applied patch: {patch.op} - {patch.reason}")
                            
                        except Exception as e:
                            error_msg = f"Failed to apply patch {patch.op}: {str(e)}"
                            errors.append(error_msg)
                            self.logger.error(error_msg)
                            # Continue with other patches
                    
                    if errors:
                        # Rollback transaction
                        tx.rollback()
                        return {
                            "success": False,
                            "message": f"Transaction rolled back due to {len(errors)} errors",
                            "errors": errors,
                            "applied": 0
                        }
                    
                    # Commit transaction
                    tx.commit()
                    return {
                        "success": True,
                        "message": f"Successfully applied {applied_count} patches",
                        "applied": applied_count,
                        "errors": []
                    }
                    
        except ServiceUnavailable as e:
            self.logger.error(f"Neo4j service unavailable: {e}")
            return {"success": False, "message": "Database service unavailable", "error": str(e)}
        except TransientError as e:
            self.logger.error(f"Neo4j transient error: {e}")
            return {"success": False, "message": "Database transient error", "error": str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected error during upsert: {e}")
            return {"success": False, "message": "Unexpected error", "error": str(e)}
    
    def query_graph(self, query: str, engine: Literal["cypher", "ngql"] = "cypher") -> List[Dict[str, Any]]:
        """
        Execute raw query against the graph database
        
        Args:
            query: The query string (Cypher or nGQL)
            engine: The query engine to use (only cypher supported for Neo4j)
            
        Returns:
            List of result rows, where each row is a dictionary
        """
        if engine != "cypher":
            raise ValueError("Neo4j only supports Cypher queries")
        
        try:
            with self._get_driver().session(database=self.database) as session:
                result = session.run(query)
                records = []
                
                for record in result:
                    # Convert Neo4j record to dictionary
                    record_dict = {}
                    for key, value in record.items():
                        # Convert Neo4j types to Python types
                        if hasattr(value, '__dict__'):
                            # Handle Neo4j node/relationship objects
                            record_dict[key] = dict(value)
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                
                return records
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    def health(self) -> Dict[str, Any]:
        """
        Check the health of the connection to the graph database
        
        Returns:
            Dictionary containing health status information
        """
        try:
            with self._get_driver().session(database=self.database) as session:
                # Simple health check query
                result = session.run("RETURN 1 as health_check")
                record = result.single()
                
                if record and record["health_check"] == 1:
                    return {
                        "status": "healthy",
                        "database": self.database,
                        "uri": self.uri,
                        "message": "Connection successful"
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "database": self.database,
                        "uri": self.uri,
                        "message": "Health check query failed"
                    }
                    
        except ServiceUnavailable:
            return {
                "status": "unhealthy",
                "database": self.database,
                "uri": self.uri,
                "message": "Service unavailable"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": self.database,
                "uri": self.uri,
                "message": f"Health check failed: {str(e)}"
            }
    
    def _patch_to_cypher(self, patch: Patch) -> str:
        """Convert a Patch to Cypher query"""
        if patch.op == "AddNode" and patch.node:
            return self._add_node_cypher(patch.node)
        elif patch.op == "UpdateProps" and patch.node:
            return self._update_props_cypher(patch.node)
        elif patch.op == "AddEdge" and patch.edge:
            return self._add_edge_cypher(patch.edge)
        elif patch.op == "Delete" and patch.node:
            return self._delete_node_cypher(patch.node)
        elif patch.op == "Delete" and patch.edge:
            return self._delete_edge_cypher(patch.edge)
        else:
            raise ValueError(f"Invalid patch operation: {patch.op}")
    
    def _add_node_cypher(self, node: NodeSpec) -> str:
        """Generate Cypher for adding a node"""
        label = node.label
        key_field = self._get_key_field(node.label)
        
        # Build properties string
        props = {key_field: node.key, **node.props}
        props_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
        
        return f"""
        MERGE (n:{label} {{{props_str}}})
        SET n += $props
        RETURN n
        """
    
    def _update_props_cypher(self, node: NodeSpec) -> str:
        """Generate Cypher for updating node properties"""
        label = node.label
        key_field = self._get_key_field(node.label)
        
        return f"""
        MATCH (n:{label} {{{key_field}: $key}})
        SET n += $props
        RETURN n
        """
    
    def _add_edge_cypher(self, edge: EdgeSpec) -> str:
        """Generate Cypher for adding an edge"""
        src_label = edge.src_label
        src_key_field = self._get_key_field(src_label)
        dst_label = edge.dst_label
        dst_key_field = self._get_key_field(dst_label)
        rel_type = edge.rel
        
        # Build properties string
        props_str = ", ".join([f"{k}: ${k}" for k in edge.props.keys()]) if edge.props else ""
        props_clause = f" {{{props_str}}}" if props_str else ""
        
        return f"""
        MATCH (src:{src_label} {{{src_key_field}: $src_key}})
        MATCH (dst:{dst_label} {{{dst_key_field}: $dst_key}})
        MERGE (src)-[r:{rel_type}{props_clause}]->(dst)
        RETURN r
        """
    
    def _delete_node_cypher(self, node: NodeSpec) -> str:
        """Generate Cypher for deleting a node"""
        label = node.label
        key_field = self._get_key_field(node.label)
        
        return f"""
        MATCH (n:{label} {{{key_field}: $key}})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
    
    def _delete_edge_cypher(self, edge: EdgeSpec) -> str:
        """Generate Cypher for deleting an edge"""
        src_label = edge.src_label
        src_key_field = self._get_key_field(src_label)
        dst_label = edge.dst_label
        dst_key_field = self._get_key_field(dst_label)
        rel_type = edge.rel
        
        return f"""
        MATCH (src:{src_label} {{{src_key_field}: $src_key}})-[r:{rel_type}]->(dst:{dst_label} {{{dst_key_field}: $dst_key}})
        DELETE r
        RETURN count(r) as deleted_count
        """
    
    def _get_key_field(self, label: str) -> str:
        """Get the key field name for a given label"""
        key_fields = {
            "Project": "id",
            "User": "id", 
            "Epic": "id",
            "Issue": "id",
            "Assignment": "id"
        }
        return key_fields.get(label, "id")
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
            self.driver = None
