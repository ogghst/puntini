"""Test for the infinite loop fix between evaluate and plan_step nodes.

This test verifies that the agent properly tracks progress and terminates
execution when the goal is complete or when the maximum step limit is reached.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from puntini.nodes.evaluate import evaluate, EvaluateResult
from puntini.nodes.message import EvaluateResponse, ExecuteToolResponse, ExecuteToolResult, Artifact
from puntini.orchestration.state_schema import State


def test_evaluate_with_step_limit():
    """Test that evaluate node escalates when step limit is exceeded."""
    # Create a mock state with current_step_count near the limit
    state = {
        "current_step_count": 10,  # At the limit
        "retry_count": 0,
        "max_retries": 3,
        "todo_list": [],
        "execute_tool_response": ExecuteToolResponse(
            current_step="evaluate",
            result=ExecuteToolResult(
                status="success",
                tool_name="test_tool",
                error=None,
                error_type=None
            ),
            progress=[],
            artifacts=[]
        )
    }
    
    # Mock the runtime to avoid LLM calls
    with patch('puntini.nodes.evaluate.get_runtime') as mock_get_runtime:
        mock_runtime = Mock()
        mock_runtime.context = {'llm': Mock()}
        mock_get_runtime.return_value = mock_runtime
        
        # Mock the LLM to avoid actual calls
        with patch.object(mock_runtime.context['llm'], 'with_structured_output') as mock_structured:
            mock_llm = Mock()
            mock_structured.return_value = mock_llm
            
            # Mock the evaluation decision
            mock_decision = Mock()
            mock_decision.decision = "advance"
            mock_decision.confidence = 0.8
            mock_decision.reasoning = "Test reasoning"
            mock_decision.goal_progress = 0.5
            mock_decision.next_action_hint = "continue"
            mock_llm.invoke.return_value = mock_decision
            
            # Call evaluate
            response = evaluate(state)
            
            # Verify that the response indicates escalation due to step limit
            assert response.current_step == "escalate"
            assert response.result.status == "error"
            assert "step_limit_exceeded" in response.result.error_type
            assert "Maximum step limit" in response.result.error


def test_evaluate_with_all_todos_completed():
    """Test that evaluate node advances to answer when all todos are completed."""
    # Create mock todos with all marked as done
    todos = [
        {"status": "done", "description": "Task 1"},
        {"status": "done", "description": "Task 2"},
        {"status": "done", "description": "Task 3"}
    ]
    
    state = {
        "current_step_count": 5,  # Below the limit
        "retry_count": 0,
        "max_retries": 3,
        "todo_list": todos,
        "execute_tool_response": ExecuteToolResponse(
            current_step="evaluate",
            result=ExecuteToolResult(
                status="success",
                tool_name="test_tool",
                error=None,
                error_type=None
            ),
            progress=[],
            artifacts=[]
        )
    }
    
    # Mock the runtime to avoid LLM calls
    with patch('puntini.nodes.evaluate.get_runtime') as mock_get_runtime:
        mock_runtime = Mock()
        mock_runtime.context = {'llm': Mock()}
        mock_get_runtime.return_value = mock_runtime
        
        # Mock the LLM to avoid actual calls
        with patch.object(mock_runtime.context['llm'], 'with_structured_output') as mock_structured:
            mock_llm = Mock()
            mock_structured.return_value = mock_llm
            
            # Create a simple object for the evaluation decision instead of Mock
            from types import SimpleNamespace
            mock_decision = SimpleNamespace(
                decision="advance",
                confidence=0.8,
                reasoning="Test reasoning",
                goal_progress=0.5,  # Below 0.9 threshold
                next_action_hint="continue"
            )
            mock_llm.invoke.return_value = mock_decision
            
            # Call evaluate
            response = evaluate(state)
            
            # Verify that the response advances to answer due to completed todos
            assert response.current_step == "answer"
            assert response.result.goal_complete is True


def test_evaluate_with_incomplete_todos():
    """Test that evaluate node continues planning when todos are incomplete."""
    # Create mock todos with some marked as planned
    todos = [
        {"status": "done", "description": "Task 1"},
        {"status": "planned", "description": "Task 2"},
        {"status": "planned", "description": "Task 3"}
    ]
    
    state = {
        "current_step_count": 5,  # Below the limit
        "retry_count": 0,
        "max_retries": 3,
        "todo_list": todos,
        "execute_tool_response": ExecuteToolResponse(
            current_step="evaluate",
            result=ExecuteToolResult(
                status="success",
                tool_name="test_tool",
                error=None,
                error_type=None
            ),
            progress=[],
            artifacts=[]
        )
    }
    
    # Mock the runtime to avoid LLM calls
    with patch('puntini.nodes.evaluate.get_runtime') as mock_get_runtime:
        mock_runtime = Mock()
        mock_runtime.context = {'llm': Mock()}
        mock_get_runtime.return_value = mock_runtime
        
        # Mock the LLM to avoid actual calls
        with patch.object(mock_runtime.context['llm'], 'with_structured_output') as mock_structured:
            mock_llm = Mock()
            mock_structured.return_value = mock_llm
            
            # Mock the evaluation decision
            mock_decision = Mock()
            mock_decision.decision = "advance"
            mock_decision.confidence = 0.8
            mock_decision.reasoning = "Test reasoning"
            mock_decision.goal_progress = 0.5  # Below 0.9 threshold
            mock_decision.next_action_hint = "continue"
            # Configure the Mock object to return the correct value for goal_progress
            type(mock_decision).goal_progress = property(lambda self: 0.5)
            mock_llm.invoke.return_value = mock_decision
            
            # Call evaluate
            response = evaluate(state)
            
            # Verify that the response continues to plan_step
            assert response.current_step == "plan_step"
            assert response.result.goal_complete is False


if __name__ == "__main__":
    test_evaluate_with_step_limit()
    test_evaluate_with_all_todos_completed()
    test_evaluate_with_incomplete_todos()
    print("All tests passed!")
