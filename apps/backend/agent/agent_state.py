from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from models.graph import Patch

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
