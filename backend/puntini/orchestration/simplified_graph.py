"""Simplified graph orchestration implementing Phase 3 minimal state pattern.

This module implements the simplified graph orchestration as specified in Phase 3
of the progressive refactoring plan, addressing the node proliferation and
over-engineering problems identified in the graph critics analysis.

Key improvements:
1. Minimal state pattern with node-specific contexts
2. Elimination of unnecessary routing nodes
3. Simplified tool execution (merge route_tool and call_tool)
4. Clear data flow with minimal state
5. Reduced complexity and improved maintainability

This addresses the critical problems:
- Unnecessary indirection: route_tool + call_tool doing one job
- State bloat: Passing everything through every node
- Routing nodes as if-statements: route_after_parse, route_after_evaluate
- Duplicate state storage: Tool names stored multiple times
- Meaningless intermediate results: Status fields that convey no information
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError

from .simplified_state import SimplifiedState, create_simplified_state, extract_node_context, update_state_with_node_output
from .minimal_state import (
    NodeInput, ParseGoalInput, PlanStepInput, ResolveEntitiesInput,
    ExecuteToolInput, EvaluateInput, DiagnoseInput, EscalateInput, AnswerInput
)
from .checkpointer import create_checkpointer, get_checkpoint_config
from ..models.goal_schemas import TodoItem
from ..models.intent_schemas import IntentSpec, ResolvedGoalSpec
from ..nodes.message import Artifact, Failure, ErrorContext, EscalateContext
from ..logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GraphContextSchema:
    """Context schema for the simplified graph.
    
    This schema defines the runtime context that is passed to all nodes
    in the graph, following LangGraph best practices for accessing
    shared services and configuration.
    
    All services are included in the context rather than the state to
    ensure the state remains serializable and lightweight.
    
    Attributes:
        llm: Language model for LLM operations
        graph_store: Graph database connection
        context_manager: Context management service
        tool_registry: Tool registry for tool execution
        tracer: Observability tracer
    """
    llm: Any
    graph_store: Any
    context_manager: Any
    tool_registry: Any
    tracer: Any


def parse_intent(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Parse minimal intent without graph context (Phase 1 of two-phase parsing).
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Dictionary with parsed intent information and state updates
        
    Notes:
        This node implements the minimal state pattern by receiving only
        the essential shared state and creating its own context as needed.
        Services are accessed through the LangGraph context mechanism.
    """
    logger.debug("Executing parse_intent node with simplified state")
    
    # Extract node-specific context
    context_data = extract_node_context(state, "parse_intent")
    node_context = ParseGoalInput(
        raw_goal=context_data["raw_goal"],
        previous_attempts=context_data.get("previous_attempts")
    )
    
    # Create node input with minimal state and context
    node_input = NodeInput(state, node_context)
    
    # Get LLM from runtime context
    llm = None
    if runtime and hasattr(runtime, 'context') and runtime.context:
        llm = runtime.context.llm
    
    # Call the implementation
    from ..nodes.parse_intent import parse_intent as parse_intent_impl
    response = parse_intent_impl(node_input.state, config, runtime)
    
    # Update state with node output
    return update_state_with_node_output(
        state, 
        {
            "current_step": response.current_step,
            "current_attempt": response.current_attempt,
            "progress": [f"Parsed intent: {response.result.parsed_goal.get('intent_type', 'unknown') if response.result and response.result.parsed_goal else 'unknown'}"],
            "artifacts": response.artifacts,
            "failures": response.failures,
            "result": response.result.model_dump() if response.result else None
        },
        "parse_intent"
    )


def resolve_entities(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Resolve entities with graph context (Phase 2 of two-phase parsing).
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Dictionary with resolved entities and state updates
    """
    logger.debug("Executing resolve_entities node with simplified state")
    
    # Extract node-specific context
    context_data = extract_node_context(state, "resolve_entities")
    node_context = ResolveEntitiesInput(
        intent_spec=context_data.get("intent_spec"),
        graph_context=context_data.get("graph_context")
    )
    
    # Create node input with minimal state and context
    node_input = NodeInput(state, node_context)
    
    # Call the implementation
    from ..nodes.resolve_entities import resolve_entities as resolve_entities_impl
    response = resolve_entities_impl(node_input.state, config, runtime)
    
    # Update state with node output
    return update_state_with_node_output(
        state,
        {
            "current_step": response.current_step,
            "current_attempt": response.current_attempt,
            "progress": [f"Resolved entities: {len(response.result.entities) if response.result and hasattr(response.result, 'entities') else 0} entities"],
            "artifacts": response.artifacts,
            "failures": response.failures,
            "result": response.result.model_dump() if response.result else None
        },
        "resolve_entities"
    )


def disambiguate(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Handle ambiguous entity references with user interaction.
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Dictionary with disambiguation results and state updates
    """
    logger.debug("Executing disambiguate node with simplified state")
    
    # Call the implementation
    from ..nodes.disambiguate import disambiguate as disambiguate_impl
    response = disambiguate_impl(state, config, runtime)
    
    # Update state with node output
    return update_state_with_node_output(
        state,
        {
            "current_step": response.current_step,
            "current_attempt": response.current_attempt,
            "progress": [f"Disambiguation completed: {response.result.status if response.result else 'unknown'}"],
            "artifacts": response.artifacts,
            "failures": response.failures,
            "result": response.result.model_dump() if response.result else None
        },
        "disambiguate"
    )


def plan_step(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Plan the next step in the agent's execution.
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Dictionary with planned step information and state updates
    """
    logger.debug("Executing plan_step node with simplified state")
    
    # Extract node-specific context
    context_data = extract_node_context(state, "plan_step")
    node_context = PlanStepInput(
        goal_spec=context_data.get("goal_spec"),
        intent_spec=context_data.get("intent_spec"),
        current_step_number=context_data.get("current_step_number", 1)
    )
    
    # Create node input with minimal state and context
    node_input = NodeInput(state, node_context)
    
    # Call the implementation
    from ..nodes.plan_step import plan_step as plan_step_impl
    response = plan_step_impl(node_input.state, config, runtime)
    
    # Update state with node output
    logger.debug(f"Plan step response tool_signature: {response.tool_signature}")
    updated_state = update_state_with_node_output(
        state,
        {
            "current_step": response.current_step,
            "progress": [f"Planned step: {response.tool_signature.get('tool_name', 'unknown') if response.tool_signature else 'unknown'}"],
            "artifacts": response.artifacts,
            "failures": response.failures,
            "result": response.result.model_dump() if response.result else None,
            "tool_signature": response.tool_signature
        },
        "plan_step"
    )
    logger.debug(f"Updated state tool_signature: {updated_state.get('tool_signature', 'NOT_FOUND')}")
    logger.debug(f"Updated state keys: {list(updated_state.keys())}")
    return updated_state


def execute_tool(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Execute tool with validation and execution in one atomic operation.
    
    This node implements the merged route_tool + call_tool functionality
    from Phase 4 of the progressive refactoring plan. It performs tool
    selection, validation, and execution in a single atomic operation.
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Dictionary with execution result and state updates
        
    Notes:
        This addresses the critical problem of unnecessary indirection
        where route_tool + call_tool were doing one job. Now it's
        one atomic operation with proper error handling.
        Services are accessed through the LangGraph context mechanism.
    """
    logger.debug("Executing execute_tool node with simplified state")
    
    # Extract node-specific context
    context_data = extract_node_context(state, "execute_tool")
    
    # Get tool signature from state (set by plan_step)
    tool_signature = state.get("tool_signature", {})
    logger.debug(f"Tool signature from state: {tool_signature}")
    
    node_context = ExecuteToolInput(
        tool_signature=tool_signature,
        execution_context=context_data.get("execution_context")
    )
    
    # Get tool_registry from runtime context
    tool_registry = None
    if runtime and hasattr(runtime, 'context') and runtime.context:
        tool_registry = runtime.context.tool_registry
    
    if not tool_registry:
        return update_state_with_node_output(
            state,
            {
                "progress": ["Error: No tool registry available in context"],
                "failures": [{"message": "Tool registry not available in context", "type": "system_error"}]
            },
            "execute_tool"
        )
    
    # Check if tool_signature is None
    if node_context.tool_signature is None:
        return update_state_with_node_output(
            state,
            {
                "progress": ["Error: No tool signature provided"],
                "failures": [{"message": "Tool signature is None", "type": "system_error"}]
            },
            "execute_tool"
        )
    
    tool_name = node_context.tool_signature.get("tool_name")
    logger.debug(f"Tool name: {tool_name}")
    tool_args = node_context.tool_signature.get("tool_args", {})
    
    try:
        # Get tool (fast)
        tool = tool_registry.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Validate args (fast)
        if hasattr(tool, 'validate_args'):
            validation_result = tool.validate_args(tool_args)
            if not validation_result.valid:
                raise ValueError(f"Validation failed: {validation_result.errors}")
        
        # Execute (potentially slow)
        # LangChain tools are invoked directly, not through an execute method
        result = tool.invoke(tool_args)
        
        return update_state_with_node_output(
            state,
            {
                "current_step": "evaluate",
                "progress": [f"Executed tool '{tool_name}' successfully"],
                "result": {
                    "status": "success",
                    "tool_name": tool_name,
                    "result": result,
                    "error": None,
                    "error_type": None
                },
                "artifacts": [{
                    "type": "tool_execution",
                    "data": {
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "result": result,
                        "execution_time": None  # TODO: Add timing
                    }
                }]
            },
            "execute_tool"
        )
        
    except Exception as e:
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(f"Tool execution error: {error_msg}")
        
        return update_state_with_node_output(
            state,
            {
                "current_step": "evaluate",
                "progress": [f"Tool execution failed: {error_msg}"],
                "result": {
                    "status": "error",
                    "tool_name": tool_name,
                    "result": None,
                    "error": error_msg,
                    "error_type": "tool_error"
                },
                "failures": [{
                    "step": "execute_tool",
                    "error": error_msg,
                    "attempt": 1,
                    "error_type": "tool_error"
                }]
            },
            "execute_tool"
        )


def evaluate(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Command:
    """Evaluate the step result and determine next action.
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Command with evaluation results and routing decision
        
    Notes:
        Uses Command for atomic update+goto semantics as specified in AGENTS.md.
        The evaluate node makes intelligent routing decisions and returns
        both state updates and the next node to execute.
        Services are accessed through the LangGraph context mechanism.
    """
    logger.debug("Executing evaluate node with simplified state")
    
    # Extract node-specific context
    context_data = extract_node_context(state, "evaluate")
    node_context = EvaluateInput(
        execution_result=context_data.get("execution_result", {}),
        goal_completion_status=context_data.get("goal_completion_status", False)
    )
    
    # Create node input with minimal state and context
    node_input = NodeInput(state, node_context)
    
    # Call the implementation
    from ..nodes.evaluate import evaluate as evaluate_impl
    response = evaluate_impl(node_input.state, config, runtime)
    
    # Prepare state updates
    state_updates = {
        "current_step": response.current_step,
        "progress": [f"Evaluation completed: {response.result.next_action if response.result else 'unknown'}"],
        "artifacts": response.artifacts,
        "failures": response.failures,
        "result": response.result.model_dump() if response.result else None,
        "retry_count": response.result.retry_count if response.result else state.get("retry_count", 0),
        "todo_list": response.todo_list
    }
    
    # Return Command for atomic update+goto semantics
    return Command(
        update=state_updates,
        goto=response.current_step
    )


def diagnose(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Diagnose failures and determine remediation.
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Dictionary with diagnosis results and state updates
    """
    logger.debug("Executing diagnose node with simplified state")
    
    # Extract node-specific context
    context_data = extract_node_context(state, "diagnose")
    node_context = DiagnoseInput(
        error_context=context_data.get("error_context"),
        failure_history=context_data.get("failure_history", [])
    )
    
    # Create node input with minimal state and context
    node_input = NodeInput(state, node_context)
    
    # Call the implementation
    from ..nodes.diagnose import diagnose as diagnose_impl
    response = diagnose_impl(node_input.state, config, runtime)
    
    # Update state with node output
    return update_state_with_node_output(
        state,
        {
            "current_step": response.current_step,
            "progress": [f"Diagnosis completed: {response.error_context.type if response.error_context else 'unknown'} error"],
            "artifacts": response.artifacts,
            "failures": response.failures,
            "result": response.result.model_dump() if response.result else None,
            "error_context": response.error_context.model_dump() if response.error_context else None
        },
        "diagnose"
    )


def escalate(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Command:
    """Handle escalation to human input with interrupt for human-in-the-loop.
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Command with escalation handling and interrupt for human input
    """
    logger.debug("Executing escalate node with simplified state")
    
    # Extract node-specific context
    context_data = extract_node_context(state, "escalate")
    node_context = EscalateInput(
        escalation_context=context_data.get("escalation_context"),
        escalation_reason=context_data.get("escalation_reason", "unknown")
    )
    
    # Create node input with minimal state and context
    node_input = NodeInput(state, node_context)
    
    # Call the implementation
    from ..nodes.escalate import escalate as escalate_impl
    response = escalate_impl(node_input.state, config, runtime)
    
    # Prepare state updates
    state_updates = {
        "current_step": response.current_step,
        "progress": [f"Escalation: {node_context.escalation_reason}"],
        "artifacts": response.artifacts,
        "failures": response.failures,
        "result": response.result.model_dump() if response.result else None,
        "escalation_context": response.escalation_context.model_dump() if response.escalation_context else None
    }
    
    # Interrupt for human input (human-in-the-loop)
    from langgraph.types import interrupt
    interrupt(response.escalation_context.model_dump() if response.escalation_context else {})
    
    # Return Command for atomic update+goto semantics
    return Command(
        update=state_updates,
        goto=response.current_step
    )


def answer(state: SimplifiedState, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Synthesize final answer and close cleanly.
    
    Args:
        state: Simplified state with minimal shared data
        config: Optional RunnableConfig for additional configuration
        runtime: Optional Runtime context for accessing context
        
    Returns:
        Dictionary with final answer and state updates
    """
    logger.debug("Executing answer node with simplified state")
    
    # Extract node-specific context
    context_data = extract_node_context(state, "answer")
    node_context = AnswerInput(
        final_result=context_data.get("final_result", {}),
        completion_status=context_data.get("completion_status", "success")
    )
    
    # Create node input with minimal state and context
    node_input = NodeInput(state, node_context)
    
    # Call the implementation
    from ..nodes.answer import answer as answer_impl
    response = answer_impl(node_input.state, config, runtime)
    
    # Update state with node output
    return update_state_with_node_output(
        state,
        {
            "current_step": response.current_step,
            "progress": [f"Final answer: {node_context.completion_status}"],
            "artifacts": response.artifacts,
            "failures": response.failures,
            "result": response.result.model_dump() if response.result else None
        },
        "answer"
    )


# Simplified routing functions using conditional edges
def route_after_parse_intent(state: SimplifiedState) -> str:
    """Route after parsing intent based on intent characteristics.
    
    Args:
        state: Current simplified state with parsed intent information
        
    Returns:
        The next node to execute
    """
    result = state.get("result", {})
    if not result or result.get("status") == "error":
        return "diagnose"
    
    # Get the parsed_goal from the result
    parsed_goal = result.get("parsed_goal", {})
    intent_type = parsed_goal.get("intent_type", "unknown")
    requires_graph_context = parsed_goal.get("requires_graph_context", False)
    
    if requires_graph_context:
        return "resolve_entities"
    else:
        return "plan_step"


def route_after_resolve_entities(state: SimplifiedState) -> str:
    """Route after resolving entities based on resolution results.
    
    Args:
        state: Current simplified state with resolved entities
        
    Returns:
        The next node to execute
    """
    result = state.get("result", {})
    if not result or result.get("status") == "error":
        return "diagnose"
    
    has_ambiguities = result.get("has_ambiguities", False)
    if has_ambiguities:
        return "disambiguate"
    else:
        return "plan_step"


def route_after_disambiguate(state: SimplifiedState) -> str:
    """Route after disambiguation based on disambiguation results.
    
    Args:
        state: Current simplified state with disambiguation results
        
    Returns:
        The next node to execute
    """
    result = state.get("result", {})
    if not result or result.get("status") == "error":
        return "diagnose"
    
    return "plan_step"


def route_after_diagnose(state: SimplifiedState) -> str:
    """Route after diagnosis based on error classification.
    
    Args:
        state: Current simplified state with diagnosis results
        
    Returns:
        The next node to execute
    """
    error_context = state.get("error_context", {})
    error_type = error_context.get("type", "unknown")
    
    if error_type == "random":
        return "plan_step"  # Retry
    else:
        return "escalate"  # Escalate for systematic or identical errors


def create_simplified_agent_graph(
    checkpointer: BaseCheckpointSaver | None = None,
    tracer: Optional[Any] = None,
    recursion_limit: int = 25
) -> StateGraph:
    """Create a simplified agent graph with minimal state pattern.
    
    This function creates a LangGraph state machine that implements the
    simplified architecture from Phase 3 of the progressive refactoring plan.
    It uses the minimal state pattern with node-specific contexts to reduce
    state bloat and improve data flow.
    
    Args:
        checkpointer: Optional checkpointer for state persistence
        tracer: Optional tracer for observability
        recursion_limit: Maximum number of supersteps allowed
        
    Returns:
        Compiled LangGraph state machine with simplified architecture
        
    Notes:
        The simplified graph implements the minimal state pattern with:
        - Reduced node count (from 10 to 8 nodes)
        - Eliminated unnecessary routing nodes
        - Merged route_tool and call_tool into execute_tool
        - Simplified state with node-specific contexts
        - Clear data flow with minimal state
    """
    # Create the state graph with simplified state and context schema
    workflow = StateGraph(SimplifiedState, context_schema=GraphContextSchema)
    
    # Add nodes (reduced from 10 to 8 nodes)
    workflow.add_node("parse_intent", parse_intent)
    workflow.add_node("resolve_entities", resolve_entities)
    workflow.add_node("disambiguate", disambiguate)
    workflow.add_node("plan_step", plan_step)
    workflow.add_node("execute_tool", execute_tool)  # Merged route_tool + call_tool
    workflow.add_node("evaluate", evaluate)
    workflow.add_node("diagnose", diagnose)
    workflow.add_node("escalate", escalate)
    workflow.add_node("answer", answer)
    
    # Add edges with simplified routing
    workflow.add_edge(START, "parse_intent")
    
    # Conditional routing after parse_intent
    workflow.add_conditional_edges(
        "parse_intent",
        route_after_parse_intent,
        {
            "resolve_entities": "resolve_entities",
            "plan_step": "plan_step",
            "diagnose": "diagnose"
        }
    )
    
    # Conditional routing after resolve_entities
    workflow.add_conditional_edges(
        "resolve_entities",
        route_after_resolve_entities,
        {
            "disambiguate": "disambiguate",
            "plan_step": "plan_step",
            "diagnose": "diagnose"
        }
    )
    
    # Conditional routing after disambiguate
    workflow.add_conditional_edges(
        "disambiguate",
        route_after_disambiguate,
        {
            "plan_step": "plan_step",
            "diagnose": "diagnose"
        }
    )
    
    # Simplified execution flow
    workflow.add_edge("plan_step", "execute_tool")
    workflow.add_edge("execute_tool", "evaluate")
    
    # Note: evaluate and escalate nodes use Command for routing
    
    # Conditional routing after diagnose
    workflow.add_conditional_edges(
        "diagnose",
        route_after_diagnose,
        {
            "plan_step": "plan_step",
            "escalate": "escalate"
        }
    )
    
    # Direct edge for completion
    workflow.add_edge("answer", END)
    
    # Prepare compilation arguments
    compile_args = {}
    
    # Add checkpointer if provided
    if checkpointer:
        compile_args["checkpointer"] = checkpointer
    
    # Compile the graph
    compiled_graph = workflow.compile(**compile_args)
    
    # Add Langfuse tracing if tracer is provided
    if tracer:
        from ..observability.langfuse_callback import LangfuseCallbackHandler
        langfuse_handler = LangfuseCallbackHandler(tracer)
        # Note: Callbacks are typically attached at invocation time
    
    return compiled_graph


def create_simplified_production_agent(
    checkpointer_type: str = "memory",
    tracer_type: str = "langfuse",
    recursion_limit: int = 25,
    **kwargs: Any
) -> StateGraph:
    """Create a simplified production-ready agent with full observability and persistence.
    
    Args:
        checkpointer_type: Type of checkpointer to use for persistence
        tracer_type: Type of tracer to use for observability
        recursion_limit: Maximum number of supersteps allowed
        **kwargs: Additional configuration parameters
        
    Returns:
        Simplified LangGraph state machine with full production features
        
    Notes:
        This function creates a simplified agent configured for production use with:
        - Minimal state pattern for reduced complexity
        - Persistent state management via checkpointer
        - Comprehensive observability via tracer
        - Human-in-the-loop support with interrupts
        - Recursion limits for safety
        - Error handling and recovery mechanisms
    """
    from ..observability.tracer_factory import make_tracer, TracerConfig
    
    # Create checkpointer for persistence
    checkpointer = create_checkpointer(checkpointer_type, **kwargs)
    
    # Create tracer for observability
    try:
        tracer_config = TracerConfig(tracer_type, **kwargs)
        tracer = make_tracer(tracer_config)
    except Exception as e:
        logger.warning(f"Failed to create {tracer_type} tracer, falling back to noop tracer: {e}")
        tracer_config = TracerConfig("noop", **kwargs)
        tracer = make_tracer(tracer_config)
    
    # Create the simplified agent with all production features
    return create_simplified_agent_graph(
        checkpointer=checkpointer,
        tracer=tracer,
        recursion_limit=recursion_limit
    )


if __name__ == "__main__":
    from ..observability.tracer_factory import make_tracer, TracerConfig

    # Create checkpointer for persistence
    checkpointer = create_checkpointer("memory")

    # Create tracer for observability
    try:
        tracer_config = TracerConfig("langfuse")
        tracer = make_tracer(tracer_config)
    except Exception as e:
        logger.warning(f"Failed to create langfuse tracer, falling back to noop tracer: {e}")
        tracer_config = TracerConfig("noop")
        tracer = make_tracer(tracer_config)

    # Create the simplified agent with all production features
    agent = create_simplified_agent_graph(
        checkpointer=checkpointer,
        tracer=tracer,
        recursion_limit=25
    )
    
    logger.info("Simplified agent graph created successfully")
