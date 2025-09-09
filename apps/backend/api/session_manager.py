"""
Session management infrastructure for handling user interactions.

This module provides the core infrastructure for managing individual user sessions
between the backend and frontend, including agent registration, message routing,
and resource management.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

from config.config import get_config


class SessionError(Exception):
    """Base exception for session-related errors."""
    pass


class SessionNotFoundError(SessionError):
    """Raised when a session is not found."""
    pass


class SessionTimeoutError(SessionError):
    """Raised when a session operation times out."""
    pass


class SessionManager:
    """
    Manages user sessions and provides core infrastructure for handling
    individual user interactions between the backend and frontend.
    
    Main responsibilities:
    - Session Lifecycle: Handles creation, retrieval, and cleanup of user sessions
    - Concurrency Control: Uses async locks to ensure thread-safe session management
    - Agent Registration: Automatically registers all available agents
    - Message Routing: Facilitates communication between the frontend and multi-agent system
    - Resource Cleanup: Ensures proper cleanup of queues and runtime resources
    - Error Handling: Robust error handling with timeouts and graceful degradation
    - Project Context: Maintains project-specific state and task management per session
    """

    def __init__(self):
        self._sessions: dict[UUID, Session] = {}
        self._session_locks: dict[UUID, asyncio.Lock] = {}
        self._cleanup_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()
        self._config = get_config()
        self._logger = logging.getLogger(__name__)

        # Session configuration
        self._session_timeout = self._config.get("session_timeout", 3600)  # 1 hour default
        self._cleanup_interval = self._config.get("cleanup_interval", 300)  # 5 minutes default
        self._max_sessions = self._config.get("max_sessions", 1000)

        # Agent registry for automatic registration
        self._agent_registry: dict[str, Any] = {}

    async def start(self):
        """Start the session manager and begin cleanup tasks."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._logger.info("Session manager started")

    async def stop(self):
        """Stop the session manager and cleanup all sessions."""
        self._shutdown_event.set()

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Cleanup all sessions
        session_ids = list(self._sessions.keys())
        for session_id in session_ids:
            await self.destroy_session(session_id)

        self._logger.info("Session manager stopped")

    async def create_session(
        self,
        user_id: str,
        project_id: UUID | None = None,
        metadata: dict[str, Any] | None = None
    ) -> "Session":
        """
        Create a new user session.
        
        Args:
            user_id: Unique identifier for the user
            project_id: Optional project context for the session
            metadata: Optional metadata for the session
            
        Returns:
            Session: The created session instance
            
        Raises:
            SessionError: If session creation fails
        """
        # Import here to avoid circular import
        from .user_session import UserSession as Session

        if len(self._sessions) >= self._max_sessions:
            # Remove oldest session if at capacity
            await self._cleanup_oldest_session()

        session_id = uuid4()

        try:
            # Create session lock
            session_lock = asyncio.Lock()
            self._session_locks[session_id] = session_lock

            # Create session
            session = Session(
                session_id=session_id,
                user_id=user_id,
                project_id=project_id,
                metadata=metadata or {},
                manager=self
            )

            # Initialize session
            await session.initialize()

            # Store session
            self._sessions[session_id] = session

            self._logger.info(f"Created session {session_id} for user {user_id}")
            return session

        except Exception as e:
            # Cleanup on failure
            if session_id in self._session_locks:
                del self._session_locks[session_id]
            raise SessionError(f"Failed to create session: {e}") from e

    async def get_session(self, session_id: UUID) -> "Session":
        """
        Retrieve an existing session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Session: The session instance
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(f"Session {session_id} not found")

        session = self._sessions[session_id]

        # Check if session is still valid
        if session.is_expired():
            await self.destroy_session(session_id)
            raise SessionNotFoundError(f"Session {session_id} has expired")

        return session

    async def destroy_session(self, session_id: UUID) -> bool:
        """
        Destroy a session and cleanup its resources.
        
        Args:
            session_id: The session identifier
            
        Returns:
            bool: True if session was destroyed, False if not found
        """
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]

        try:
            # Cleanup session resources
            await session.cleanup()

            # Remove from registry
            del self._sessions[session_id]

            # Remove session lock
            if session_id in self._session_locks:
                del self._session_locks[session_id]

            self._logger.info(f"Destroyed session {session_id}")
            return True

        except Exception as e:
            self._logger.error(f"Error destroying session {session_id}: {e}")
            return False

    async def list_sessions(self, user_id: str | None = None) -> list["Session"]:
        """
        List all active sessions, optionally filtered by user.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List[Session]: List of active sessions
        """
        sessions = list(self._sessions.values())

        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]

        return sessions

    def register_agent(self, agent_name: str, agent_class: Any):
        """
        Register an agent class for automatic session initialization.
        
        Args:
            agent_name: Name of the agent
            agent_class: Agent class to register
        """
        self._agent_registry[agent_name] = agent_class
        self._logger.info(f"Registered agent: {agent_name}")

    def get_agent_registry(self) -> dict[str, Any]:
        """Get the current agent registry."""
        return self._agent_registry.copy()

    async def _cleanup_loop(self):
        """Background task for cleaning up expired sessions."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        expired_sessions = []

        for session_id, session in self._sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.destroy_session(session_id)

        if expired_sessions:
            self._logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def _cleanup_oldest_session(self):
        """Remove the oldest session when at capacity."""
        if not self._sessions:
            return

        # Find oldest session by creation time
        oldest_session_id = min(
            self._sessions.keys(),
            key=lambda sid: self._sessions[sid].created_at
        )

        await self.destroy_session(oldest_session_id)
        self._logger.info(f"Removed oldest session {oldest_session_id} due to capacity limit")

    @asynccontextmanager
    async def session_lock(self, session_id: UUID):
        """Context manager for session-level locking."""
        if session_id not in self._session_locks:
            raise SessionNotFoundError(f"Session {session_id} not found")

        async with self._session_locks[session_id]:
            yield

    @property
    def session_count(self) -> int:
        """Get the current number of active sessions."""
        return len(self._sessions)

    @property
    def max_sessions(self) -> int:
        """Get the maximum number of sessions allowed."""
        return self._max_sessions


# Global session manager instance
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
