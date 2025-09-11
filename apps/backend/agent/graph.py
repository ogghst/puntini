from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .agent_state import AgentState
from models.graph import Patch
from tools.tool_registry import ToolRegistry
from context.context_manager import AdaptiveContextManager
from graphstore.store import GraphStore
from config.config import get_config

class StatefulProjectAgent:
    """Main agent with persistent state management"""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        context_manager: AdaptiveContextManager,
        graph_store: GraphStore,
        observability_service: Any,
        checkpointer=None
    ):
        self.tool_registry = tool_registry
        self.context_manager = context_manager
        self.graph_store = graph_store
        self.observability = observability_service
        self.checkpointer = checkpointer or MemorySaver()

        # Initialize tools from registry
        self.tool_registry.discover_and_register_plugins()

        # Create the workflow
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow with all nodes"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("planning", self.planning_node)
        workflow.add_node("tool_selection", self.tool_selection_node)
        workflow.add_node("extraction", self.extraction_node)
        workflow.add_node("validation", self.validation_node)
        workflow.add_node("execution", self.execution_node)
        workflow.add_node("evaluation", self.evaluation_node)
        workflow.add_node("answer_generation", self.answer_generation_node)

        # Set entry point
        workflow.set_entry_point("planning")

        # Define edges
        workflow.add_edge("planning", "tool_selection")
        workflow.add_edge("tool_selection", "extraction")
        workflow.add_edge("extraction", "validation")
        workflow.add_edge("validation", "execution")
        workflow.add_edge("execution", "evaluation")

        # Conditional routing from evaluation
        def evaluation_router(state: AgentState) -> str:
            # Check escalation first
            # should_escalate, reason, context = self.context_manager.should_escalate(state)

            # if should_escalate:
            #     state["escalated"] = True
            #     state["escalation_reason"] = reason
            #     return "answer_generation"

            # Check completion
            if state["current_step_index"] >= len(state["execution_plan"]):
                return "answer_generation"

            # Check if we need to retry or continue
            if state["last_error"]:
                return "tool_selection"  # Retry with new tool selection
            else:
                # Advance to next step
                state["current_step_index"] += 1
                state["retry_count"] = 0  # Reset for new step
                return "tool_selection"

        workflow.add_conditional_edges(
            "evaluation",
            evaluation_router,
            {
                "tool_selection": "tool_selection",
                "answer_generation": "answer_generation"
            }
        )

        workflow.add_edge("answer_generation", END)

        return workflow

    async def process_request(self, user_goal: str, thread_id: str) -> Dict:
        """Process user request with persistent state"""
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "messages": [], "user_goal": user_goal, "execution_plan": [],
            "current_step_index": 0, "retry_count": 0, "last_error": None,
            "error_history": [], "failure_pattern": None, "pending_patches": [],
            "selected_tools": [], "tool_outputs": {}, "context_level": 0,
            "escalation_signals": [], "escalated": False, "escalation_reason": None,
            "applied_operations": [], "final_result": None
        }
        result = await self.app.ainvoke(initial_state, config)

        return result["final_result"]

    def planning_node(self, state: AgentState) -> Dict:
        return {"execution_plan": ["placeholder step 1", "placeholder step 2"]}

    def tool_selection_node(self, state: AgentState) -> Dict:
        return {"selected_tools": []}

    def extraction_node(self, state: AgentState) -> Dict:
        return {"pending_patches": []}

    def validation_node(self, state: AgentState) -> Dict:
        return {"last_error": None}

    def execution_node(self, state: AgentState) -> Dict:
        return {"applied_operations": []}

    def evaluation_node(self, state: AgentState) -> Dict:
        return {}

    def answer_generation_node(self, state: AgentState) -> Dict:
        return {"final_result": {"response": "Completed."}}

    def _handle_validation_failure(self, state: AgentState, errors: List[str], stage: str) -> Dict:
        error_message = f"{stage.title()} validation failed: {'; '.join(errors)}"
        return {
            "last_error": error_message,
            "retry_count": state["retry_count"] + 1,
            "error_history": state["error_history"] + [error_message],
        }
