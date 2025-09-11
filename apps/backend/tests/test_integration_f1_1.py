"""
Integration test for F1-1: Complete Extract→Validate→Upsert→Answer flow
Demonstrates the full workflow with real components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any

# Mock the LLM service at module level to prevent initialization errors
@pytest.fixture(autouse=True)
def mock_llm_service():
    """Automatically mock LLM service for all tests in this module"""
    with patch('services.llm_service.get_llm_service') as mock_get_llm, \
         patch('tools.extraction_tools.get_llm_service') as mock_tools_llm:
        
        mock_llm_instance = Mock()
        mock_llm_instance.generate_text = Mock(return_value=Mock(
            success=True,
            content='{"execution_plan": ["Extract entities", "Validate data", "Apply changes"]}'
        ))
        mock_llm_instance.generate_structured_output = Mock(return_value=Mock(
            success=True,
            content='{"entities": []}'
        ))
        
        mock_get_llm.return_value = mock_llm_instance
        mock_tools_llm.return_value = mock_llm_instance
        yield mock_llm_instance

from agent.graph import StatefulProjectAgent
from tools.tool_registry import ToolRegistry
from context.context_manager import AdaptiveContextManager
from graphstore.neo4j_store import Neo4jStore
from tools.extraction_tools import (
    ProjectExtractionTool, UserExtractionTool, 
    EpicExtractionTool, IssueExtractionTool
)


class TestF1Integration:
    """Integration test for the complete F1-1 workflow"""
    
    @pytest.fixture
    def mock_neo4j_store(self):
        """Create a mock Neo4j store for testing"""
        store = Mock(spec=Neo4jStore)
        store.upsert = Mock(return_value={"success": True, "applied": 1, "message": "Success"})
        store.health = Mock(return_value={"status": "healthy"})
        return store
    
    @pytest.fixture
    def tool_registry_with_tools(self):
        """Create tool registry with extraction tools"""
        registry = ToolRegistry()
        
        # Register extraction tools
        registry.register_tool(
            tool_instance=ProjectExtractionTool(),
            plugin_name="project_extraction",
            version="1.0.0"
        )
        registry.register_tool(
            tool_instance=UserExtractionTool(),
            plugin_name="user_extraction", 
            version="1.0.0"
        )
        registry.register_tool(
            tool_instance=EpicExtractionTool(),
            plugin_name="epic_extraction",
            version="1.0.0"
        )
        registry.register_tool(
            tool_instance=IssueExtractionTool(),
            plugin_name="issue_extraction",
            version="1.0.0"
        )
        
        return registry
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager"""
        return AdaptiveContextManager()
    
    @pytest.fixture
    def observability_service(self):
        """Create mock observability service"""
        return Mock()
    
    @pytest.fixture
    def agent(self, tool_registry_with_tools, context_manager, mock_neo4j_store, observability_service):
        """Create agent with all dependencies"""
        return StatefulProjectAgent(
            tool_registry=tool_registry_with_tools,
            context_manager=context_manager,
            graph_store=mock_neo4j_store,
            observability_service=observability_service
        )
    
    @pytest.mark.asyncio
    async def test_project_creation_workflow(self, agent, mock_neo4j_store):
        """Test complete workflow for project creation"""
        # Mock LLM service responses
        with patch('agent.graph.get_llm_service') as mock_llm:
            mock_llm_instance = Mock()
            
            # Mock planning response
            mock_llm_instance.generate_text = Mock(side_effect=[
                Mock(success=True, content='["Extract project from user input", "Validate extracted data", "Apply changes to knowledge graph", "Generate response"]'),
                Mock(success=True, content="I've successfully created the project 'Test Project' with all required entities and relationships.")
            ])
            
            mock_llm.return_value = mock_llm_instance
            
            # Test the workflow
            result = await agent.process_request(
                user_goal="Create a new project called 'Test Project' for customer portal development",
                thread_id="test-thread-456"
            )
            
            # Verify result
            assert result is not None
            assert "response" in result
            assert "success" in result
            
            # Verify graph store was called
            mock_neo4j_store.upsert.assert_called()
    
    @pytest.mark.asyncio
    async def test_epic_creation_workflow(self, agent, mock_neo4j_store):
        """Test complete workflow for epic creation"""
        with patch('agent.graph.get_llm_service') as mock_llm:
            mock_llm_instance = Mock()
            
            mock_llm_instance.generate_text = Mock(side_effect=[
                Mock(success=True, content='["Extract epic from user input", "Validate extracted data", "Apply changes to knowledge graph", "Generate response"]'),
                Mock(success=True, content="I've successfully created the epic 'User Authentication' for project PROJ-TEST.")
            ])
            
            mock_llm.return_value = mock_llm_instance
            
            result = await agent.process_request(
                user_goal="Create an epic called 'User Authentication' for the Test Project",
                thread_id="test-thread-789"
            )
            
            assert result is not None
            assert "response" in result
            assert "success" in result
            
            mock_neo4j_store.upsert.assert_called()
    
    @pytest.mark.asyncio
    async def test_issue_creation_workflow(self, agent, mock_neo4j_store):
        """Test complete workflow for issue creation"""
        with patch('agent.graph.get_llm_service') as mock_llm:
            mock_llm_instance = Mock()
            
            mock_llm_instance.generate_text = Mock(side_effect=[
                Mock(success=True, content='["Extract issue from user input", "Validate extracted data", "Apply changes to knowledge graph", "Generate response"]'),
                Mock(success=True, content="I've successfully created the issue 'Login Form Validation' for epic EPIC-UAE.")
            ])
            
            mock_llm.return_value = mock_llm_instance
            
            result = await agent.process_request(
                user_goal="Create an issue called 'Login Form Validation' for the User Authentication epic",
                thread_id="test-thread-101"
            )
            
            assert result is not None
            assert "response" in result
            assert "success" in result
            
            mock_neo4j_store.upsert.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, agent, mock_neo4j_store):
        """Test error handling in the workflow"""
        # Mock LLM service to return error
        with patch('agent.graph.get_llm_service') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm_instance.generate_text = Mock(return_value=Mock(
                success=False,
                content="",
                error="LLM service unavailable"
            ))
            mock_llm.return_value = mock_llm_instance
            
            # Mock graph store to return error
            mock_neo4j_store.upsert = Mock(return_value={
                "success": False,
                "message": "Database connection failed",
                "error": "Connection timeout"
            })
            
            result = await agent.process_request(
                user_goal="Create a new project",
                thread_id="test-thread-error"
            )
            
            # Should still return a result, but with error information
            assert result is not None
            assert "response" in result
            # The agent should handle errors gracefully
    
    @pytest.mark.asyncio
    async def test_validation_failure_workflow(self, agent, mock_neo4j_store):
        """Test validation failure handling"""
        with patch('agent.graph.get_llm_service') as mock_llm:
            mock_llm_instance = Mock()
            
            mock_llm_instance.generate_text = Mock(side_effect=[
                Mock(success=True, content='["Extract entities", "Validate data", "Apply changes", "Generate response"]'),
                Mock(success=True, content="I encountered validation errors while processing your request.")
            ])
            
            mock_llm.return_value = mock_llm_instance
            
            # Mock validation pipeline to return failure
            with patch('agent.graph.ValidationPipeline') as mock_validation:
                mock_validation_instance = Mock()
                mock_validation_instance.validate_patches = Mock(return_value=Mock(
                    success=False,
                    stage="schema",
                    errors=["Invalid node specification"],
                    validated_patches=[]
                ))
                mock_validation.return_value = mock_validation_instance
                
                result = await agent.process_request(
                    user_goal="Create invalid project data",
                    thread_id="test-thread-validation"
                )
                
                assert result is not None
                assert "response" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
