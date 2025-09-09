"""
Unit tests for session management functionality.

This module contains tests for SessionManager and Session classes
to ensure proper session lifecycle management and message handling.
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

# Add the parent directory to the Python path to allow for relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from api.session_manager import SessionManager, SessionNotFoundError
from api.user_session import UserSession as Session
from models.session import SessionStatus


class TestSessionManager:
    """Test cases for SessionManager class."""

    @pytest_asyncio.fixture
    async def session_manager(self):
        """Create a session manager instance for testing."""
        manager = SessionManager()
        await manager.start()
        try:
            yield manager
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test session creation."""
        user_id = "test_user"
        project_id = uuid4()

        session = await session_manager.create_session(
            user_id=user_id,
            project_id=project_id,
            metadata={"test": "data"}
        )

        assert session.user_id == user_id
        assert session.project_id == project_id
        assert session.metadata["test"] == "data"
        assert session.status == SessionStatus.ACTIVE
        assert session_manager.session_count == 1

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager):
        """Test session retrieval."""
        user_id = "test_user"
        session = await session_manager.create_session(user_id=user_id)

        retrieved_session = await session_manager.get_session(session.session_id)
        assert retrieved_session.session_id == session.session_id
        assert retrieved_session.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_manager):
        """Test retrieval of non-existent session."""
        with pytest.raises(SessionNotFoundError):
            await session_manager.get_session(uuid4())

    @pytest.mark.asyncio
    async def test_destroy_session(self, session_manager):
        """Test session destruction."""
        session = await session_manager.create_session("test_user")
        session_id = session.session_id

        success = await session_manager.destroy_session(session_id)
        assert success is True
        assert session_manager.session_count == 0

        with pytest.raises(SessionNotFoundError):
            await session_manager.get_session(session_id)

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_manager):
        """Test session listing."""
        # Create multiple sessions
        session1 = await session_manager.create_session("user1")
        session2 = await session_manager.create_session("user2")
        session3 = await session_manager.create_session("user1")

        # List all sessions
        all_sessions = await session_manager.list_sessions()
        assert len(all_sessions) == 3

        # List sessions for specific user
        user1_sessions = await session_manager.list_sessions(user_id="user1")
        assert len(user1_sessions) == 2
        assert all(s.user_id == "user1" for s in user1_sessions)

    @pytest.mark.asyncio
    async def test_agent_registration(self, session_manager):
        """Test agent registration."""
        class MockAgent:
            def __init__(self, session):
                self.session = session

        session_manager.register_agent("mock_agent", MockAgent)
        registry = session_manager.get_agent_registry()

        assert "mock_agent" in registry
        assert registry["mock_agent"] == MockAgent


class TestSession:
    """Test cases for Session class."""

    @pytest.fixture
    def session(self):
        """Create a session instance for testing."""
        return Session(
            session_id=uuid4(),
            user_id="test_user",
            project_id=uuid4(),
            metadata={"test": "data"}
        )

    @pytest.mark.asyncio
    async def test_session_initialization(self, session):
        """Test session initialization."""
        await session.initialize()

        assert session.status == SessionStatus.ACTIVE
        assert session.is_active() is True
        assert session.is_expired() is False

    @pytest.mark.asyncio
    async def test_message_sending(self, session):
        """Test message sending to session."""
        await session.initialize()

        message_id = await session.send_message(
            content="Hello, world!",
            message_type="user",
            metadata={"test": "message"}
        )

        assert message_id is not None
        assert session.last_activity > session.created_at

    @pytest.mark.asyncio
    async def test_message_receiving(self, session):
        """Test message receiving from session."""
        await session.initialize()

        # Send a message
        await session.send_message("Test message", "user")

        # Receive the message
        message = await session.receive_message(timeout=1.0)
        assert message is not None
        assert message.content == "Test message"
        assert message.message_type == "user"

    @pytest.mark.asyncio
    async def test_project_context_management(self, session):
        """Test project context management."""
        await session.initialize()

        # Update context
        context = {"project_name": "Test Project", "status": "active"}
        await session.update_project_context(context)

        # Get context
        retrieved_context = await session.get_project_context()
        assert retrieved_context == context

    @pytest.mark.asyncio
    async def test_task_management(self, session):
        """Test task management."""
        await session.initialize()

        # Add tasks
        task1 = {"title": "Task 1", "description": "First task"}
        task2 = {"title": "Task 2", "description": "Second task"}

        await session.add_task(task1)
        await session.add_task(task2)

        # Get tasks
        tasks = await session.get_tasks()
        assert len(tasks) == 2
        assert tasks[0].title == "Task 1"
        assert tasks[1].title == "Task 2"

    @pytest.mark.asyncio
    async def test_session_expiration(self, session):
        """Test session expiration."""
        # Set expiration to past time
        session.expires_at = datetime.now(UTC) - timedelta(seconds=1)

        assert session.is_expired() is True
        assert session.is_active() is False

    @pytest.mark.asyncio
    async def test_session_cleanup(self, session):
        """Test session cleanup."""
        await session.initialize()

        # Add some data
        await session.update_project_context({"test": "data"})
        await session.add_task({"title": "Test task"})

        # Cleanup
        await session.cleanup()

        assert session.status == SessionStatus.EXPIRED
        assert session._cleanup_complete.is_set()


if __name__ == "__main__":
    pytest.main([__file__])
