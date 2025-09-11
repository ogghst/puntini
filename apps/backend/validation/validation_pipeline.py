"""
Validation pipeline for Extract→Validate→Upsert→Answer flow.
Implements Schema → Domain → Graph constraint validation.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from pydantic import ValidationError
from models.graph import Patch, NodeSpec, EdgeSpec
from models.domain import Project, User, Epic, Issue
from graphstore.store import GraphStore


class ValidationStage(Enum):
    """Validation stages in the pipeline"""
    SCHEMA = "schema"
    DOMAIN = "domain"
    GRAPH_CONSTRAINTS = "graph_constraints"


class ValidationResult:
    """Result of validation operation"""
    def __init__(
        self,
        success: bool,
        stage: ValidationStage,
        errors: List[str] = None,
        warnings: List[str] = None,
        validated_patches: List[Patch] = None
    ):
        self.success = success
        self.stage = stage
        self.errors = errors or []
        self.warnings = warnings or []
        self.validated_patches = validated_patches or []


class ValidationPipeline:
    """Multi-stage validation pipeline for patches"""
    
    def __init__(self, graph_store: GraphStore):
        self.graph_store = graph_store
        self.logger = logging.getLogger(__name__)
        
        # Domain model mapping
        self.domain_models = {
            "Project": Project,
            "User": User,
            "Epic": Epic,
            "Issue": Issue
        }
    
    async def validate_patches(self, patches: List[Patch]) -> ValidationResult:
        """
        Validate patches through the complete pipeline
        
        Args:
            patches: List of patches to validate
            
        Returns:
            ValidationResult with success status and details
        """
        if not patches:
            return ValidationResult(
                success=True,
                stage=ValidationStage.SCHEMA,
                warnings=["No patches to validate"]
            )
        
        # Stage 1: Schema Validation
        schema_result = self._validate_schema(patches)
        if not schema_result.success:
            return schema_result
        
        # Stage 2: Domain Validation
        domain_result = self._validate_domain(schema_result.validated_patches)
        if not domain_result.success:
            return domain_result
        
        # Stage 3: Graph Constraints Validation
        graph_result = await self._validate_graph_constraints(domain_result.validated_patches)
        if not graph_result.success:
            return graph_result
        
        return ValidationResult(
            success=True,
            stage=ValidationStage.GRAPH_CONSTRAINTS,
            validated_patches=graph_result.validated_patches,
            warnings=schema_result.warnings + domain_result.warnings + graph_result.warnings
        )
    
    def _validate_schema(self, patches: List[Patch]) -> ValidationResult:
        """Stage 1: Validate patch schema and structure"""
        errors = []
        warnings = []
        validated_patches = []
        
        for i, patch in enumerate(patches):
            try:
                # Validate patch structure
                if not patch.op:
                    errors.append(f"Patch {i}: Missing operation")
                    continue
                
                if patch.op in ["AddNode", "UpdateProps"] and not patch.node:
                    errors.append(f"Patch {i}: Node operation requires node specification")
                    continue
                
                if patch.op in ["AddEdge"] and not patch.edge:
                    errors.append(f"Patch {i}: Edge operation requires edge specification")
                    continue
                
                if patch.op == "Delete" and not patch.node and not patch.edge:
                    errors.append(f"Patch {i}: Delete operation requires node or edge specification")
                    continue
                
                # Validate node specification if present
                if patch.node:
                    node_errors = self._validate_node_spec(patch.node, i)
                    errors.extend(node_errors)
                
                # Validate edge specification if present
                if patch.edge:
                    edge_errors = self._validate_edge_spec(patch.edge, i)
                    errors.extend(edge_errors)
                
                if not errors:
                    validated_patches.append(patch)
                
            except Exception as e:
                errors.append(f"Patch {i}: Unexpected error during schema validation: {str(e)}")
        
        return ValidationResult(
            success=len(errors) == 0,
            stage=ValidationStage.SCHEMA,
            errors=errors,
            warnings=warnings,
            validated_patches=validated_patches
        )
    
    def _validate_domain(self, patches: List[Patch]) -> ValidationResult:
        """Stage 2: Validate domain model constraints"""
        errors = []
        warnings = []
        validated_patches = []
        
        for i, patch in enumerate(patches):
            try:
                if patch.op in ["AddNode", "UpdateProps"] and patch.node:
                    # Validate against domain model
                    domain_errors = self._validate_node_domain(patch.node, i)
                    errors.extend(domain_errors)
                
                if not domain_errors:
                    validated_patches.append(patch)
                
            except Exception as e:
                errors.append(f"Patch {i}: Unexpected error during domain validation: {str(e)}")
        
        return ValidationResult(
            success=len(errors) == 0,
            stage=ValidationStage.DOMAIN,
            errors=errors,
            warnings=warnings,
            validated_patches=validated_patches
        )
    
    async def _validate_graph_constraints(self, patches: List[Patch]) -> ValidationResult:
        """Stage 3: Validate graph constraints and relationships"""
        errors = []
        warnings = []
        validated_patches = []
        
        try:
            # Check for constraint violations
            constraint_errors = await self._check_constraint_violations(patches)
            errors.extend(constraint_errors)
            
            # Check for relationship consistency
            relationship_errors = await self._check_relationship_consistency(patches)
            errors.extend(relationship_errors)
            
            if not errors:
                validated_patches = patches
                
        except Exception as e:
            errors.append(f"Graph constraint validation failed: {str(e)}")
        
        return ValidationResult(
            success=len(errors) == 0,
            stage=ValidationStage.GRAPH_CONSTRAINTS,
            errors=errors,
            warnings=warnings,
            validated_patches=validated_patches
        )
    
    def _validate_node_spec(self, node: NodeSpec, patch_index: int) -> List[str]:
        """Validate node specification"""
        errors = []
        
        # Check required fields
        if not node.label:
            errors.append(f"Patch {patch_index}: Node label is required")
        
        if not node.key:
            errors.append(f"Patch {patch_index}: Node key is required")
        
        # Check label validity
        valid_labels = ["Project", "User", "Epic", "Issue", "Assignment"]
        if node.label and node.label not in valid_labels:
            errors.append(f"Patch {patch_index}: Invalid node label '{node.label}'. Must be one of: {valid_labels}")
        
        # Check key field consistency
        if node.label and node.key:
            expected_key_field = self._get_expected_key_field(node.label)
            if expected_key_field and expected_key_field not in node.props:
                # Add the key to props if missing
                node.props[expected_key_field] = node.key
        
        return errors
    
    def _validate_edge_spec(self, edge: EdgeSpec, patch_index: int) -> List[str]:
        """Validate edge specification"""
        errors = []
        
        # Check required fields
        if not edge.src_label:
            errors.append(f"Patch {patch_index}: Source label is required")
        
        if not edge.src_key:
            errors.append(f"Patch {patch_index}: Source key is required")
        
        if not edge.dst_label:
            errors.append(f"Patch {patch_index}: Destination label is required")
        
        if not edge.dst_key:
            errors.append(f"Patch {patch_index}: Destination key is required")
        
        if not edge.rel:
            errors.append(f"Patch {patch_index}: Relationship type is required")
        
        # Check relationship validity
        valid_relationships = [
            "HAS_EPIC", "HAS_ISSUE", "ASSIGNED_TO", "BLOCKS",
            "HAS_ASSIGNMENT", "ASSIGNMENT_OF"
        ]
        if edge.rel and edge.rel not in valid_relationships:
            errors.append(f"Patch {patch_index}: Invalid relationship '{edge.rel}'. Must be one of: {valid_relationships}")
        
        return errors
    
    def _validate_node_domain(self, node: NodeSpec, patch_index: int) -> List[str]:
        """Validate node against domain model"""
        errors = []
        
        if node.label not in self.domain_models:
            return errors  # Skip validation for unknown labels
        
        try:
            # Create domain model instance for validation
            domain_model = self.domain_models[node.label]
            
            # Prepare data for validation
            validation_data = {
                "key": node.key,
                **node.props
            }
            
            # Validate using Pydantic
            domain_model(**validation_data)
            
        except ValidationError as e:
            for error in e.errors():
                field = error.get("loc", ["unknown"])[0]
                message = error.get("msg", "Validation error")
                errors.append(f"Patch {patch_index}: Domain validation failed for {field}: {message}")
        
        except Exception as e:
            errors.append(f"Patch {patch_index}: Domain validation error: {str(e)}")
        
        return errors
    
    async def _check_constraint_violations(self, patches: List[Patch]) -> List[str]:
        """Check for constraint violations in the graph"""
        errors = []
        
        # Check for duplicate keys
        node_keys = {}
        for patch in patches:
            if patch.op in ["AddNode"] and patch.node:
                label = patch.node.label
                key = patch.node.key
                
                if label not in node_keys:
                    node_keys[label] = set()
                
                if key in node_keys[label]:
                    errors.append(f"Duplicate key '{key}' for label '{label}'")
                else:
                    node_keys[label].add(key)
        
        return errors
    
    async def _check_relationship_consistency(self, patches: List[Patch]) -> List[str]:
        """Check for relationship consistency"""
        errors = []
        
        # Check that referenced nodes exist or are being created
        referenced_nodes = set()
        created_nodes = set()
        
        # First pass: collect all nodes being created
        for patch in patches:
            if patch.op == "AddNode" and patch.node:
                created_nodes.add((patch.node.label, patch.node.key))
        
        # Second pass: check relationships
        for patch in patches:
            if patch.op == "AddEdge" and patch.edge:
                src_ref = (patch.edge.src_label, patch.edge.src_key)
                dst_ref = (patch.edge.dst_label, patch.edge.dst_key)
                
                # Check if source node is being created
                if src_ref not in created_nodes:
                    referenced_nodes.add(src_ref)
                
                # Check if destination node is being created
                if dst_ref not in created_nodes:
                    referenced_nodes.add(dst_ref)
        
        # For now, we'll allow referenced nodes to exist in the graph
        # In a full implementation, we'd check the graph store
        
        return errors
    
    def _get_expected_key_field(self, label: str) -> Optional[str]:
        """Get the expected key field for a label"""
        key_fields = {
            "Project": "id",
            "User": "user_id",
            "Epic": "id",
            "Issue": "id",
            "Assignment": "id"
        }
        return key_fields.get(label)
