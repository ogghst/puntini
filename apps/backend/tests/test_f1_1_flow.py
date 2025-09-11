"""
Test for F1-1: Extract→Validate→Upsert→Answer flow
Tests the complete workflow for Project, Epic, Issue, User entities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Mock the LLM service at module level to prevent initialization errors
@pytest.fixture(autouse=True)
def mock_llm_service():
    """Automatically mock LLM service for all tests in this module"""
    with patch('services.llm_service.get_llm_service') as mock_get_llm, \
         patch('tools.extraction_tools.get_llm_service') as mock_tools_llm:
        
        mock_llm_instance = Mock()
        mock_llm_instance.generate_text = AsyncMock(return_value=Mock(
            success=True,
            content='{"execution_plan": ["Extract entities", "Validate data", "Apply changes"]}'
        ))
        mock_llm_instance.generate_structured_output = AsyncMock(return_value=Mock(
            success=True,
            content='{"entities": []}'
        ))
        
        mock_get_llm.return_value = mock_llm_instance
        mock_tools_llm.return_value = mock_llm_instance
        yield mock_llm_instance

from agent.graph import StatefulProjectAgent
from agent.agent_state import AgentState
from tools.tool_registry import ToolRegistry
from context.context_manager import AdaptiveContextManager
from graphstore.neo4j_store import Neo4jStore
from models.graph import Patch, NodeSpec, EdgeSpec
from models.domain import Project, User, Epic, Issue


class TestF1Flow:
    """Test the complete F1-1 workflow"""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        # Mock tool registry
        tool_registry = Mock(spec=ToolRegistry)
        tool_registry.discover_and_register_plugins = Mock()
        tool_registry.get_available_tools = Mock(return_value=[])
        
        # Mock context manager
        context_manager = Mock(spec=AdaptiveContextManager)
        context_manager.should_escalate = Mock(return_value=(False, None, None))
        
        # Mock graph store
        graph_store = Mock(spec=Neo4jStore)
        graph_store.upsert = Mock(return_value={"success": True, "applied": 1})
        
        # Mock observability service
        observability_service = Mock()
        
        return {
            "tool_registry": tool_registry,
            "context_manager": context_manager,
            "graph_store": graph_store,
            "observability_service": observability_service
        }
    
    @pytest.fixture
    def agent(self, mock_services):
        """Create agent instance with mocked services"""
        return StatefulProjectAgent(
            tool_registry=mock_services["tool_registry"],
            context_manager=mock_services["context_manager"],
            graph_store=mock_services["graph_store"],
            observability_service=mock_services["observability_service"]
        )
    
    @pytest.mark.asyncio
    async def test_planning_node(self, agent):
        """Test planning node generates execution plan"""
        state = {
            "user_goal": "Create a new project called 'Test Project' with a user authentication epic",
            "execution_plan": [],
            "current_step_index": 0,
            "retry_count": 0,
            "last_error": None,
            "error_history": [],
            "failure_pattern": None,
            "pending_patches": [],
            "selected_tools": [],
            "tool_outputs": {},
            "context_level": 0,
            "escalation_signals": [],
            "escalated": False,
            "escalation_reason": None,
            "applied_operations": [],
            "final_result": None
        }
        
        result = await agent.planning_node(state)
        
        assert "execution_plan" in result
        assert isinstance(result["execution_plan"], list)
        assert len(result["execution_plan"]) > 0
    
    @pytest.mark.asyncio
    async def test_tool_selection_node(self, agent):
        """Test tool selection node selects appropriate tools"""
        state = {
            "user_goal": "Create a new project",
            "execution_plan": ["Extract entities from user input", "Validate data", "Apply changes"],
            "current_step_index": 0,
            "retry_count": 0,
            "last_error": None,
            "error_history": [],
            "failure_pattern": None,
            "pending_patches": [],
            "selected_tools": [],
            "tool_outputs": {},
            "context_level": 0,
            "escalation_signals": [],
            "escalated": False,
            "escalation_reason": None,
            "applied_operations": [],
            "final_result": None
        }
        
        result = await agent.tool_selection_node(state)
        
        assert "selected_tools" in result
        assert isinstance(result["selected_tools"], list)
    
    @pytest.mark.asyncio
    async def test_extraction_node(self, agent):
        """Test extraction node processes user input"""
        state = {
            "user_goal": "Create a new project called 'Test Project'",
            "execution_plan": ["Extract entities", "Validate data", "Apply changes"],
            "current_step_index": 1,
            "retry_count": 0,
            "last_error": None,
            "error_history": [],
            "failure_pattern": None,
            "pending_patches": [],
            "selected_tools": [],
            "tool_outputs": {},
            "context_level": 0,
            "escalation_signals": [],
            "escalated": False,
            "escalation_reason": None,
            "applied_operations": [],
            "final_result": None
        }
        
        result = await agent.extraction_node(state)
        
        assert "pending_patches" in result
        assert "tool_outputs" in result
        assert isinstance(result["pending_patches"], list)
        assert isinstance(result["tool_outputs"], dict)
    
    @pytest.mark.asyncio
    async def test_validation_node(self, agent):
        """Test validation node validates patches"""
        # Create test patches
        test_patches = [
            Patch(
                op="AddNode",
                node=NodeSpec(
                    label="Project",
                    key="PROJ-TEST",
                    props={"nome": "Test Project", "descrizione": "A test project"}
                ),
                reason="Test project creation"
            )
        ]
        
        state = {
            "user_goal": "Create a new project",
            "execution_plan": ["Extract entities", "Validate data", "Apply changes"],
            "current_step_index": 2,
            "retry_count": 0,
            "last_error": None,
            "error_history": [],
            "failure_pattern": None,
            "pending_patches": test_patches,
            "selected_tools": [],
            "tool_outputs": {},
            "context_level": 0,
            "escalation_signals": [],
            "escalated": False,
            "escalation_reason": None,
            "applied_operations": [],
            "final_result": None
        }
        
        result = await agent.validation_node(state)
        
        assert "pending_patches" in result
        assert isinstance(result["pending_patches"], list)
    
    @pytest.mark.asyncio
    async def test_execution_node(self, agent, mock_services):
        """Test execution node applies patches to graph store"""
        # Create test patches
        test_patches = [
            Patch(
                op="AddNode",
                node=NodeSpec(
                    label="Project",
                    key="PROJ-TEST",
                    props={"nome": "Test Project", "descrizione": "A test project"}
                ),
                reason="Test project creation"
            )
        ]
        
        state = {
            "user_goal": "Create a new project",
            "execution_plan": ["Extract entities", "Validate data", "Apply changes"],
            "current_step_index": 3,
            "retry_count": 0,
            "last_error": None,
            "error_history": [],
            "failure_pattern": None,
            "pending_patches": test_patches,
            "selected_tools": [],
            "tool_outputs": {},
            "context_level": 0,
            "escalation_signals": [],
            "escalated": False,
            "escalation_reason": None,
            "applied_operations": [],
            "final_result": None
        }
        
        result = await agent.execution_node(state)
        
        assert "applied_operations" in result
        assert isinstance(result["applied_operations"], list)
        
        # Verify graph store was called
        mock_services["graph_store"].upsert.assert_called_once_with(test_patches)
    
    @pytest.mark.asyncio
    async def test_evaluation_node(self, agent):
        """Test evaluation node determines next steps"""
        state = {
            "user_goal": "Create a new project",
            "execution_plan": ["Extract entities", "Validate data", "Apply changes"],
            "current_step_index": 3,
            "retry_count": 0,
            "last_error": None,
            "error_history": [],
            "failure_pattern": None,
            "pending_patches": [],
            "selected_tools": [],
            "tool_outputs": {},
            "context_level": 0,
            "escalation_signals": [],
            "escalated": False,
            "escalation_reason": None,
            "applied_operations": [{"patches": [], "result": {"success": True}}],
            "final_result": None
        }
        
        result = await agent.evaluation_node(state)
        
        # Should return empty dict to continue workflow
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_answer_generation_node(self, agent):
        """Test answer generation node creates final response"""
        state = {
            "user_goal": "Create a new project called 'Test Project'",
            "execution_plan": ["Extract entities", "Validate data", "Apply changes"],
            "current_step_index": 3,
            "retry_count": 0,
            "last_error": None,
            "error_history": [],
            "failure_pattern": None,
            "pending_patches": [],
            "selected_tools": [],
            "tool_outputs": {},
            "context_level": 0,
            "escalation_signals": [],
            "escalated": False,
            "escalation_reason": None,
            "applied_operations": [{"patches": [], "result": {"success": True}}],
            "final_result": None
        }
        
        result = await agent.answer_generation_node(state)
        
        assert "final_result" in result
        assert isinstance(result["final_result"], dict)
        assert "response" in result["final_result"]
        assert "success" in result["final_result"]
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, agent, mock_services):
        """Test the complete workflow end-to-end"""
        # Mock the LLM service responses
        with patch('agent.graph.get_llm_service') as mock_llm:
            mock_llm_instance = Mock()
            mock_llm_instance.generate_text = AsyncMock(return_value=Mock(
                success=True,
                content='["Extract entities from user input", "Validate extracted data", "Apply changes to knowledge graph", "Generate response"]'
            ))
            mock_llm.return_value = mock_llm_instance
            
            # Test the complete workflow
            result = await agent.process_request(
                user_goal="Create a new project called 'Test Project'",
                thread_id="test-thread-123"
            )
            
            assert result is not None
            assert "response" in result
            assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__])
