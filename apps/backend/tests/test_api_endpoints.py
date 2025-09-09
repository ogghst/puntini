"""
Unit tests for API endpoints.

This module contains comprehensive tests for all FastAPI endpoints
to ensure proper functionality, error handling, and response validation.
"""

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

# Add the parent directory to the Python path to allow for relative imports
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from main import create_app
from api.session_manager import SessionManager


@pytest.fixture(autouse=True)
def reset_session_manager():
    """
    Reset the session manager singleton before each test to ensure test isolation.
    """
    SessionManager._instance = None


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    """
    app = create_app()
    return TestClient(app)


@pytest.fixture
async def session_manager():
    """
    Create and start a session manager for testing.
    """
    manager = SessionManager()
    await manager.start()
    try:
        yield manager
    finally:
        await manager.stop()


class TestHealthEndpoints:
    """Test cases for health-related endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns correct information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Hello World!"
        assert data["api"] == "Business Improvement Project Management API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        """Test the health endpoint returns correct status."""
        response = client.get("/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "business-improvement-api"
        assert data["version"] == "0.1.0"
        assert "components" in data
        assert data["components"]["api"] == "operational"

    def test_health_endpoint_redirect(self, client):
        """Test that /health redirects to /health/."""
        response = client.get("/health", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "http://testserver/health/"


class TestSessionEndpoints:
    """Test cases for session management endpoints."""

    def test_create_session_success(self, client):
        """Test successful session creation."""
        session_data = {
            "user_id": "test_user_123",
            "project_id": str(uuid4()),
            "metadata": {"test": "data"}
        }
        
        response = client.post("/sessions/", json=session_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data
        assert data["user_id"] == session_data["user_id"]
        assert data["project_id"] == session_data["project_id"]
        assert data["status"] == "active"
        assert data["is_active"] is True

    def test_create_session_minimal_data(self, client):
        """Test session creation with minimal required data."""
        session_data = {
            "user_id": "minimal_user"
        }
        
        response = client.post("/sessions/", json=session_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == session_data["user_id"]
        assert data["status"] == "active"

    def test_create_session_invalid_data(self, client):
        """Test session creation with invalid data."""
        # Missing required user_id
        session_data = {
            "project_id": str(uuid4())
        }
        
        response = client.post("/sessions/", json=session_data)
        assert response.status_code == 422

    def test_get_session_success(self, client):
        """Test successful session retrieval."""
        # First create a session
        session_data = {"user_id": "test_user"}
        create_response = client.post("/sessions/", json=session_data)
        assert create_response.status_code == 200
        
        session_id = create_response.json()["session_id"]
        
        # Then retrieve it
        response = client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert data["user_id"] == "test_user"

    def test_get_session_not_found(self, client):
        """Test session retrieval for non-existent session."""
        fake_session_id = str(uuid4())
        response = client.get(f"/sessions/{fake_session_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_session_invalid_uuid(self, client):
        """Test session retrieval with invalid UUID."""
        response = client.get("/sessions/invalid-uuid")
        assert response.status_code == 422

    def test_destroy_session_success(self, client):
        """Test successful session destruction."""
        # First create a session
        session_data = {"user_id": "test_user"}
        create_response = client.post("/sessions/", json=session_data)
        session_id = create_response.json()["session_id"]
        
        # Then destroy it
        response = client.delete(f"/sessions/{session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "destroyed successfully" in data["message"]

    def test_destroy_session_not_found(self, client):
        """Test session destruction for non-existent session."""
        fake_session_id = str(uuid4())
        response = client.delete(f"/sessions/{fake_session_id}")
        assert response.status_code == 404

    def test_list_sessions_empty(self, client):
        """Test listing sessions when none exist."""
        response = client.get("/sessions/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_count"] == 0
        assert data["active_count"] == 0
        assert data["sessions"] == []

    def test_list_sessions_with_data(self, client):
        """Test listing sessions with existing data."""
        # Create multiple sessions
        for i in range(3):
            session_data = {"user_id": f"user_{i}"}
            client.post("/sessions/", json=session_data)
        
        response = client.get("/sessions/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_count"] == 3
        assert data["active_count"] == 3
        assert len(data["sessions"]) == 3

    def test_list_sessions_filtered_by_user(self, client):
        """Test listing sessions filtered by user ID."""
        # Create sessions for different users
        client.post("/sessions/", json={"user_id": "user1"})
        client.post("/sessions/", json={"user_id": "user1"})
        client.post("/sessions/", json={"user_id": "user2"})
        
        # Filter by user1
        response = client.get("/sessions/?user_id=user1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_count"] == 2
        assert all(session["user_id"] == "user1" for session in data["sessions"])

    def test_session_stats(self, client):
        """Test session statistics endpoint."""
        response = client.get("/sessions/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_sessions" in data
        assert "active_sessions" in data
        assert "expired_sessions" in data
        assert "error_sessions" in data
        assert "max_sessions" in data
        assert "average_session_duration" in data

    def test_send_message_success(self, client):
        """Test sending a message to a session."""
        # Create a session first
        session_data = {"user_id": "test_user"}
        create_response = client.post("/sessions/", json=session_data)
        session_id = create_response.json()["session_id"]
        
        # Send a message
        message_data = {
            "content": "Hello, world!",
            "message_type": "user",
            "metadata": {"test": "message"}
        }
        
        response = client.post(f"/sessions/{session_id}/messages", json=message_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message_id" in data
        assert data["content"] == message_data["content"]
        assert data["message_type"] == message_data["message_type"]

    def test_send_message_session_not_found(self, client):
        """Test sending message to non-existent session."""
        fake_session_id = str(uuid4())
        message_data = {"content": "Hello", "message_type": "user"}
        
        response = client.post(f"/sessions/{fake_session_id}/messages", json=message_data)
        assert response.status_code == 404

    def test_receive_message_success(self, client):
        """Test receiving a message from a session."""
        # Create a session and send a message
        session_data = {"user_id": "test_user"}
        create_response = client.post("/sessions/", json=session_data)
        session_id = create_response.json()["session_id"]
        
        message_data = {"content": "Test message", "message_type": "user"}
        client.post(f"/sessions/{session_id}/messages", json=message_data)
        
        # Receive the message
        response = client.get(f"/sessions/{session_id}/messages")
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == "Test message"
        assert data["message_type"] == "user"

    def test_get_project_context_success(self, client):
        """Test getting project context for a session."""
        # Create a session
        session_data = {"user_id": "test_user"}
        create_response = client.post("/sessions/", json=session_data)
        session_id = create_response.json()["session_id"]
        
        response = client.get(f"/sessions/{session_id}/context")
        assert response.status_code == 200
        
        data = response.json()
        assert "project_context" in data
        assert "tasks" in data
        assert "task_count" in data

    def test_update_project_context_success(self, client):
        """Test updating project context for a session."""
        # Create a session
        session_data = {"user_id": "test_user"}
        create_response = client.post("/sessions/", json=session_data)
        session_id = create_response.json()["session_id"]
        
        # Update context
        context_data = {"project_name": "Test Project", "status": "active"}
        response = client.put(f"/sessions/{session_id}/context", json=context_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "updated successfully" in data["message"]

    def test_add_task_success(self, client):
        """Test adding a task to a session."""
        # Create a session
        session_data = {"user_id": "test_user"}
        create_response = client.post("/sessions/", json=session_data)
        session_id = create_response.json()["session_id"]
        
        # Add a task
        task_data = {"title": "Test Task", "description": "A test task"}
        response = client.post(f"/sessions/{session_id}/tasks", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "added successfully" in data["message"]

    def test_get_tasks_success(self, client):
        """Test getting tasks for a session."""
        # Create a session
        session_data = {"user_id": "test_user"}
        create_response = client.post("/sessions/", json=session_data)
        session_id = create_response.json()["session_id"]
        
        response = client.get(f"/sessions/{session_id}/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert "count" in data
        assert isinstance(data["tasks"], list)


class TestPlaceholderEndpoints:
    """Test cases for placeholder endpoints."""

    def test_agent_action_endpoint(self, client):
        """Test the agent action placeholder endpoint."""
        response = client.post("/agent/act")
        assert response.status_code == 200
        
        data = response.json()
        assert "placeholder" in data["status"]
        assert "Phase 1" in data["message"]

    def test_graph_patch_endpoint(self, client):
        """Test the graph patch placeholder endpoint."""
        response = client.post("/graph/patch")
        assert response.status_code == 200
        
        data = response.json()
        assert "placeholder" in data["status"]
        assert "Phase 1" in data["message"]

    def test_graph_query_endpoint(self, client):
        """Test the graph query placeholder endpoint."""
        response = client.get("/graph/query")
        assert response.status_code == 200
        
        data = response.json()
        assert "placeholder" in data["status"]
        assert "Phase 1" in data["message"]

    def test_todo_get_endpoint(self, client):
        """Test the TODO get placeholder endpoint."""
        response = client.get("/todo/")
        assert response.status_code == 200
        
        data = response.json()
        assert "placeholder" in data["status"]
        assert "Phase 1" in data["message"]

    def test_todo_post_endpoint(self, client):
        """Test the TODO post placeholder endpoint."""
        response = client.post("/todo/")
        assert response.status_code == 200
        
        data = response.json()
        assert "placeholder" in data["status"]
        assert "Phase 1" in data["message"]


class TestErrorHandling:
    """Test cases for error handling and edge cases."""

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/sessions/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_content_type(self, client):
        """Test handling of missing Content-Type header."""
        response = client.post("/sessions/", data='{"user_id": "test"}')
        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Test handling of unsupported HTTP methods."""
        response = client.patch("/sessions/")
        assert response.status_code == 405

    def test_large_request_body(self, client):
        """Test handling of large request bodies."""
        large_metadata = {"data": "x" * 10000}  # 10KB of data
        session_data = {
            "user_id": "test_user",
            "metadata": large_metadata
        }
        
        response = client.post("/sessions/", json=session_data)
        # Should either succeed or fail gracefully, not crash
        assert response.status_code in [200, 413, 422]


if __name__ == "__main__":
    pytest.main([__file__])
