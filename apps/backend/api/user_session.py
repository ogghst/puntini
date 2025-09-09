"""
Individual user session management.

This module provides the Session class for managing individual user sessions
with runtime orchestration and message queuing capabilities.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from api.session_manager import SessionError, SessionManager
from models.session import Message, MessageType, SessionInfo, SessionStatus, TaskInfo


class UserSession:
    """
    Manages individual user sessions with runtime orchestration and message queuing.
    
    Main responsibilities:
    - Session Management: Creates and manages individual user sessions with unique IDs
    - Runtime Orchestration: Initializes and controls the agent runtime for each session
    - Message Queuing: Manages asynchronous input/output queues for real-time communication with agents
    """

    def __init__(
        self,
        session_id: UUID,
        user_id: str,
        project_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        manager: SessionManager | None = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.project_id = project_id
        self.metadata = metadata or {}
        self.manager = manager

        # Session state
        self.status = SessionStatus.INITIALIZING
        self.created_at = datetime.now(UTC)
        self.last_activity = datetime.now(UTC)
        self.expires_at = self.created_at + timedelta(seconds=3600)  # 1 hour default

        # Message queues
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._output_queue: asyncio.Queue = asyncio.Queue()
        self._message_handlers: dict[str, Callable[[Message], Awaitable[None]]] = {}

        # Agent runtime
        self._agents: dict[str, Any] = {}
        self._agent_tasks: dict[str, asyncio.Task] = {}
        self._runtime_task: asyncio.Task | None = None

        # Project context
        self._project_context: dict[str, Any] = {}
        self._task_queue: list[TaskInfo] = []

        # Error handling
        self._error_count = 0
        self._max_errors = 5

        # Logging
        self._logger = logging.getLogger(f"{__name__}.{session_id}")

        # Cleanup flag
        self._cleanup_complete = asyncio.Event()

    async def initialize(self):
        """Initialize the session and start the agent runtime."""
        try:
            self._logger.info(f"Initializing session {self.session_id}")

            # Register default message handlers
            self._register_default_handlers()

            # Initialize agents if manager is available
            if self.manager:
                await self._initialize_agents()

            # Start runtime task
            self._runtime_task = asyncio.create_task(self._runtime_loop())

            # Update status
            self.status = SessionStatus.ACTIVE
            self.last_activity = datetime.now(UTC)

            self._logger.info(f"Session {self.session_id} initialized successfully")

        except Exception as e:
            self.status = SessionStatus.ERROR
            self._logger.error(f"Failed to initialize session {self.session_id}: {e}")
            raise SessionError(f"Session initialization failed: {e}") from e

    async def cleanup(self):
        """Cleanup session resources and stop all tasks."""
        try:
            self._logger.info(f"Cleaning up session {self.session_id}")
            self.status = SessionStatus.CLEANING_UP

            # Stop runtime task
            if self._runtime_task and not self._runtime_task.done():
                self._runtime_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._runtime_task

            # Stop agent tasks
            for _agent_name, task in self._agent_tasks.items():
                if not task.done():
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task

            # Clear queues
            self._clear_queues()

            # Clear agents
            self._agents.clear()
            self._agent_tasks.clear()

            self.status = SessionStatus.EXPIRED
            self._cleanup_complete.set()

            self._logger.info(f"Session {self.session_id} cleaned up successfully")

        except Exception as e:
            self._logger.error(f"Error cleaning up session {self.session_id}: {e}")
            self.status = SessionStatus.ERROR

    async def send_message(
        self,
        content: Any,
        message_type: MessageType = MessageType.USER,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Send a message to the session.
        
        Args:
            content: Message content
            message_type: Type of message
            metadata: Optional message metadata
            
        Returns:
            str: Message ID
        """
        message_id = f"{self.session_id}_{int(datetime.now(UTC).timestamp() * 1000)}"

        message = Message(
            id=message_id,
            content=content,
            timestamp=datetime.now(UTC),
            message_type=message_type,
            metadata=metadata or {}
        )

        await self._input_queue.put(message)
        self.last_activity = datetime.now(UTC)

        self._logger.debug(f"Sent message {message_id} to session {self.session_id}")
        return message_id

    async def receive_message(self, timeout: float | None = None) -> Message | None:
        """
        Receive a message from the session.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Message: The received message, or None if timeout
        """
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self._output_queue.get(),
                    timeout=timeout
                )
            else:
                message = await self._output_queue.get()

            self.last_activity = datetime.now(UTC)
            return message

        except TimeoutError:
            return None

    def register_message_handler(
        self,
        message_type: MessageType,
        handler: Callable[[Message], Awaitable[None]]
    ):
        """
        Register a message handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Async function to handle the message
        """
        self._message_handlers[message_type.value] = handler
        self._logger.debug(f"Registered handler for message type: {message_type.value}")

    async def get_project_context(self) -> dict[str, Any]:
        """Get the current project context."""
        return self._project_context.copy()

    async def update_project_context(self, context: dict[str, Any]):
        """Update the project context."""
        self._project_context.update(context)
        self.last_activity = datetime.now(UTC)
        self._logger.debug(f"Updated project context for session {self.session_id}")

    async def add_task(self, task_data: dict[str, Any]) -> TaskInfo:
        """Add a task to the session task queue."""
        task_id = f"{self.session_id}_{len(self._task_queue)}"
        created_at = datetime.now(UTC).isoformat()

        task = TaskInfo(
            id=task_id,
            title=task_data.get("title", "Untitled Task"),
            description=task_data.get("description"),
            status=task_data.get("status", "pending"),
            priority=task_data.get("priority", "medium"),
            created_at=created_at,
            metadata=task_data.get("metadata", {})
        )

        self._task_queue.append(task)
        self.last_activity = datetime.now(UTC)
        self._logger.debug(f"Added task to session {self.session_id}")
        return task

    async def get_tasks(self) -> list[TaskInfo]:
        """Get all tasks for this session."""
        return self._task_queue.copy()

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.now(UTC) > self.expires_at

    def is_active(self) -> bool:
        """Check if the session is active."""
        return self.status == SessionStatus.ACTIVE and not self.is_expired()

    async def _runtime_loop(self):
        """Main runtime loop for processing messages and managing agents."""
        self._logger.info(f"Starting runtime loop for session {self.session_id}")

        while self.status in [SessionStatus.ACTIVE, SessionStatus.PAUSED]:
            try:
                # Process input messages
                await self._process_input_messages()

                # Process agent outputs
                await self._process_agent_outputs()

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in runtime loop for session {self.session_id}: {e}")
                self._error_count += 1

                if self._error_count >= self._max_errors:
                    self.status = SessionStatus.ERROR
                    break

                # Wait before retrying
                await asyncio.sleep(1)

        self._logger.info(f"Runtime loop ended for session {self.session_id}")

    async def _process_input_messages(self):
        """Process messages from the input queue."""
        while not self._input_queue.empty():
            try:
                message = self._input_queue.get_nowait()
                await self._handle_message(message)
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                self._logger.error(f"Error processing input message: {e}")

    async def _process_agent_outputs(self):
        """Process outputs from agents."""
        for agent_name, agent in self._agents.items():
            try:
                if hasattr(agent, "get_output"):
                    output = await agent.get_output()
                    if output:
                        await self._output_queue.put(output)
            except Exception as e:
                self._logger.error(f"Error processing output from agent {agent_name}: {e}")

    async def _handle_message(self, message: Message):
        """Handle a message using registered handlers."""
        handler = self._message_handlers.get(message.message_type.value)

        if handler:
            try:
                await handler(message)
            except Exception as e:
                self._logger.error(f"Error handling message {message.id}: {e}")
        else:
            # Default handling - just log and forward
            self._logger.debug(f"No handler for message type {message.message_type.value}, forwarding")
            await self._output_queue.put(message)

    def _register_default_handlers(self):
        """Register default message handlers."""
        self.register_message_handler(MessageType.USER, self._handle_user_message)
        self.register_message_handler(MessageType.SYSTEM, self._handle_system_message)
        self.register_message_handler(MessageType.AGENT, self._handle_agent_message)

    async def _handle_user_message(self, message: Message):
        """Handle user messages."""
        self._logger.debug(f"Handling user message: {message.content}")
        # Forward to agents or process directly
        await self._output_queue.put(message)

    async def _handle_system_message(self, message: Message):
        """Handle system messages."""
        self._logger.debug(f"Handling system message: {message.content}")
        # Process system commands
        if isinstance(message.content, dict):
            command = message.content.get("command")
            if command == "update_context":
                await self.update_project_context(message.content.get("data", {}))
            elif command == "add_task":
                await self.add_task(message.content.get("data", {}))

    async def _handle_agent_message(self, message: Message):
        """Handle agent messages."""
        self._logger.debug(f"Handling agent message: {message.content}")
        # Process agent responses
        await self._output_queue.put(message)

    async def _initialize_agents(self):
        """Initialize agents for this session."""
        if not self.manager:
            return

        agent_registry = self.manager.get_agent_registry()

        for agent_name, agent_class in agent_registry.items():
            try:
                # Create agent instance
                agent = agent_class(session=self)
                self._agents[agent_name] = agent

                # Start agent task
                task = asyncio.create_task(agent.run())
                self._agent_tasks[agent_name] = task

                self._logger.info(f"Initialized agent {agent_name} for session {self.session_id}")

            except Exception as e:
                self._logger.error(f"Failed to initialize agent {agent_name}: {e}")

    def _clear_queues(self):
        """Clear all message queues."""
        # Clear input queue
        while not self._input_queue.empty():
            try:
                self._input_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Clear output queue
        while not self._output_queue.empty():
            try:
                self._output_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    @property
    def session_info(self) -> SessionInfo:
        """Get session information."""
        return SessionInfo(
            session_id=self.session_id,
            user_id=self.user_id,
            project_id=self.project_id,
            status=self.status,
            created_at=self.created_at,
            last_activity=self.last_activity,
            expires_at=self.expires_at,
            is_expired=self.is_expired(),
            is_active=self.is_active(),
            agent_count=len(self._agents),
            task_count=len(self._task_queue),
            metadata=self.metadata
        )
