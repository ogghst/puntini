from typing import TypedDict, Annotated, List, Optional, Literal, Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import asyncio
from models.graph import Patch
from tools.tool_registry import ToolRegistry
from context.context_manager import AdaptiveContextManager
from graphstore.store import GraphStore
from config.config import get_config


class AgentState(TypedDict):
    """Mutable state with snapshot persistence"""
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Execution tracking
    user_goal: str
    execution_plan: List[str]
    current_step_index: int
    retry_count: int
    
    # Error management
    last_error: Optional[str]
    error_history: List[str]
    failure_pattern: Optional[str]
    
    # Tool and operation state
    pending_patches: List[Patch]
    selected_tools: List[str]
    tool_outputs: Dict[str, Any]
    
    # Context and escalation
    context_level: int
    escalation_signals: List[Dict]
    escalated: bool
    escalation_reason: Optional[str]
    
    # Results
    applied_operations: List[Dict]
    final_result: Optional[Dict]

class StatefulProjectAgent:
    """Main agent with persistent state management"""
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        context_manager: AdaptiveContextManager,
        graph_store,
        observability_service,
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
            should_escalate, reason, context = self.context_manager.should_escalate(state)
            
            if should_escalate:
                state["escalated"] = True
                state["escalation_reason"] = reason
                return "answer_generation"
            
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
        config = {"configurable": {"thread_id": thread_id},
                  "callbacks": [get_config().langfuse_handler]}
        
        # Check if we have existing state for this thread
        existing_state = None
        try:
            existing_state = self.checkpointer.get(config)
        except:
            pass  # No existing state
        
        if existing_state:
            # Resume from existing state
            result = await self.app.ainvoke({}, config)
        else:
            # Initialize new conversation
            initial_state = {
                "messages": [],
                "user_goal": user_goal,
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
            result = await self.app.ainvoke(initial_state, config)
        
        return result["final_result"]
    
    def tool_selection_node(self, state: AgentState) -> Dict:
        """Select appropriate tools based on current context and history"""
        with self.observability.start_trace("tool_selection") as trace:
            try:
                # Get available tools
                available_tools = self.tool_registry.get_available_tools()
                
                # Analyze context to determine best tools
                context = self.context_manager.prepare_adaptive_context(state)
                current_step = state["execution_plan"][state["current_step_index"]] if state["execution_plan"] else "unknown"
                
                # Use LLM to select tools (implementation would use structured output)
                selected_tools = self._select_tools_with_llm(available_tools, context, current_step)
                
                trace.log_event("tools_selected", {"tools": [t.name for t in selected_tools]})
                
                return {
                    "selected_tools": [t.name for t in selected_tools],
                    "context_level": 0,  # Reset context level for new tool selection
                    "last_error": None
                }
                
            except Exception as e:
                trace.log_event("tool_selection_error", {"error": str(e)}, "ERROR")
                return {
                    "last_error": f"Tool selection failed: {str(e)}",
                    "retry_count": state["retry_count"] + 1,
                    "error_history": state["error_history"] + [str(e)]
                }
    
    def validation_node(self, state: AgentState) -> Dict:
        """Sequential validation pipeline: Schema -> Domain -> Graph constraints"""
        with self.observability.start_trace("validation_pipeline") as trace:
            try:
                patches = state["pending_patches"]
                
                # Stage 1: Schema Validation (already done by Pydantic in extraction)
                schema_errors = []  # Would be populated by Pydantic validation
                
                if schema_errors:
                    trace.log_event("schema_validation_failed", {"errors": schema_errors}, "WARN")
                    return self._handle_validation_failure(state, schema_errors, "schema")
                
                # Stage 2: Domain Validation
                domain_result = self._validate_domain_constraints(patches)
                
                if not domain_result.is_valid:
                    trace.log_event("domain_validation_failed", {"errors": domain_result.errors}, "WARN")
                    return self._handle_validation_failure(state, domain_result.errors, "domain")
                
                # Stage 3: Graph Constraint Validation
                graph_result = self.graph_store.validate_constraints(patches)
                
                if not graph_result.is_valid:
                    trace.log_event("graph_validation_failed", {"errors": graph_result.errors}, "WARN")
                    return self._handle_validation_failure(state, graph_result.errors, "graph")
                
                trace.log_event("validation_passed", {"patches": len(patches)})
                return {"last_error": None}
                
            except Exception as e:
                trace.log_event("validation_error", {"error": str(e)}, "ERROR")
                return self._handle_validation_failure(state, [str(e)], "system")
    
    def _handle_validation_failure(self, state: AgentState, errors: List[str], stage: str) -> Dict:
        """Handle validation failure with context-aware error messaging"""
        error_message = f"{stage.title()} validation failed: {'; '.join(errors)}"
        
        return {
            "last_error": error_message,
            "retry_count": state["retry_count"] + 1,
            "error_history": state["error_history"] + [error_message],
            "failure_pattern": self.context_manager._analyze_failure_pattern(
                state["error_history"] + [error_message]
            )
        }

# Usage Example
async def main():
    """Example usage of the stateful agent"""
    
    # Initialize services
    tool_registry = ToolRegistry()
    observability = ObservabilityService()  # Your observability implementation
    context_manager = AdaptiveContextManager(observability)
    graph_store = YourGraphStore()  # Your graph store implementation
    
    # Use SQLite checkpointer for persistence
    checkpointer = AsyncSqliteSaver.from_conn_string("agent_state.db")
    
    # Create agent
    agent = StatefulProjectAgent(
        tool_registry=tool_registry,
        context_manager=context_manager,
        graph_store=graph_store,
        observability_service=observability,
        checkpointer=checkpointer
    )
    
    # Process request with persistent state
    result = await agent.process_request(
        user_goal="Create an issue tracker project with 3 epics",
        thread_id="user_123_session_1"
    )
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
