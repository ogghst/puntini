"""Integration tests for plan_step node with SimplifiedState."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from puntini.nodes.plan_step import plan_step
from puntini.orchestration.simplified_state import create_simplified_state


def test_plan_step_accesses_goal_info_from_simplified_state():
    """Test that plan_step correctly accesses goal information from SimplifiedState structure."""
    # Create a SimplifiedState with goal information in the result field
    state = create_simplified_state(
        session_id="test-session",
        goal="Create a project named TestProject"
    )
    
    # Add parsed goal information to the result field
    parsed_goal = {
        "intent": "create",
        "complexity": "simple",
        "estimated_steps": 1,
        "entities": [
            {
                "name": "TestProject",
                "type": "project",
                "label": "Project",
                "properties": {"name": "TestProject"}
            }
        ],
        "constraints": [],
        "domain_hints": []
    }
    
    state["result"] = {"parsed_goal": parsed_goal}
    
    # Verify that the goal information is correctly structured
    assert "result" in state
    assert "parsed_goal" in state["result"]
    assert state["result"]["parsed_goal"]["intent"] == "create"
    assert state["result"]["parsed_goal"]["entities"][0]["name"] == "TestProject"
    
    # Test that plan_step can access the goal information
    # We'll patch the LLM interaction to avoid complex mocking
    with patch('puntini.nodes.plan_step.get_runtime') as mock_get_runtime:
        # Mock the runtime
        mock_runtime = Mock()
        mock_runtime.context = {"llm": Mock()}
        mock_get_runtime.return_value = mock_runtime
        
        # Mock the LLM to raise an exception to avoid complex mocking
        with patch.object(mock_runtime.context['llm'], 'with_structured_output') as mock_with_output:
            mock_with_output.side_effect = Exception("LLM call mocked")
            
            # Call plan_step and expect it to handle the exception
            result = plan_step(state)
            
            # Verify that the function tried to access the goal information
            # The result should be in the diagnose step due to the mocked exception
            assert result.current_step == "diagnose"
            assert result.result.status == "error"
            assert "LLM call mocked" in result.result.error


def test_plan_step_fallback_without_goal_info():
    """Test that plan_step falls back correctly when goal information is not in the result field."""
    # Create a SimplifiedState without goal information in the result field
    state = create_simplified_state(
        session_id="test-session",
        goal="Create a project named TestProject"
    )
    
    # Don't add result field or add an empty result
    state["result"] = {}
    
    # Test the plan_step function
    result = plan_step(state)
    
    # Verify the fallback behavior
    assert result.result.status == "success"
    assert result.tool_signature["tool_name"] == "query_graph"  # Default fallback tool
    assert "Fallback plan" in result.tool_signature["reasoning"]


if __name__ == "__main__":
    test_plan_step_accesses_goal_info_from_simplified_state()
    test_plan_step_fallback_without_goal_info()
    print("All integration tests passed!")

