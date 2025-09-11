from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .agent_state import AgentState
from models.graph import Patch
from tools.tool_registry import ToolRegistry
from context.context_manager import AdaptiveContextManager
from graphstore.store import GraphStore
from graphstore.neo4j_store import Neo4jStore
from validation.validation_pipeline import ValidationPipeline
from services.llm_service import get_llm_service
from prompts.extraction_prompts import ExtractionPrompts
from config.config import get_config
import logging

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
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.llm_service = get_llm_service()
        self.validation_pipeline = ValidationPipeline(graph_store)
        self.prompts = ExtractionPrompts()

        # Initialize tools from registry
        self.tool_registry.discover_and_register_plugins()

        # Create the workflow
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow with all nodes"""
        workflow = StateGraph(AgentState)

        # Add nodes (all are async now)
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
            if state.get("escalated", False):
                return "answer_generation"

            # Check completion
            if state["current_step_index"] >= len(state["execution_plan"]) - 1:
                return "answer_generation"

            # Check if we need to retry or continue
            if state.get("last_error"):
                if state.get("retry_count", 0) >= 3:
                    return "answer_generation"  # Escalate after max retries
                else:
                    return "tool_selection"  # Retry with new tool selection
            else:
                # Advance to next step
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
        config = {"configurable": {"thread_id": thread_id}, "callbacks": [get_config().langfuse_handler]}

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

    async def planning_node(self, state: AgentState) -> Dict:
        """Analyze user goal and generate execution plan"""
        try:
            self.logger.info(f"Planning for goal: {state['user_goal']}")
            
            # Use LLM to generate execution plan
            plan_response = await self.llm_service.generate_text(
                prompt_template=self.prompts.get_planning_prompt(),
                context={"user_goal": state["user_goal"]}
            )
            
            if plan_response.success:
                # Parse the plan (assuming it returns a JSON array)
                import json
                try:
                    execution_plan = json.loads(plan_response.content)
                except json.JSONDecodeError:
                    # Fallback to simple plan
                    execution_plan = [
                        "Extract entities from user input",
                        "Validate extracted data",
                        "Apply changes to knowledge graph",
                        "Generate response"
                    ]
            else:
                # Fallback plan
                execution_plan = [
                    "Extract entities from user input",
                    "Validate extracted data", 
                    "Apply changes to knowledge graph",
                    "Generate response"
                ]
            
            self.logger.info(f"Generated execution plan: {execution_plan}")
            return {"execution_plan": execution_plan}
            
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return {
                "execution_plan": ["Extract entities", "Validate data", "Apply changes", "Generate response"],
                "last_error": f"Planning error: {str(e)}"
            }

    async def tool_selection_node(self, state: AgentState) -> Dict:
        """Select appropriate tools based on current step"""
        try:
            # Don't advance step index here - it should be advanced in evaluation
            current_step = state["execution_plan"][state["current_step_index"]]
            self.logger.info(f"Selecting tools for step {state['current_step_index']}: {current_step}")
            
            selected_tools = []
            
            # Select tools based on step content
            if "extract" in current_step.lower():
                # Select extraction tools
                available_tools = self.tool_registry.get_available_tools()
                extraction_tools = [tool for tool in available_tools if "extract" in tool.name]
                selected_tools = [tool.name for tool in extraction_tools]
            
            elif "validate" in current_step.lower():
                # Validation is handled by the validation pipeline
                selected_tools = ["validation_pipeline"]
            
            elif "apply" in current_step.lower() or "graph" in current_step.lower():
                # Graph operations
                selected_tools = ["graph_store"]
            
            self.logger.info(f"Selected tools: {selected_tools}")
            return {"selected_tools": selected_tools}
            
        except Exception as e:
            self.logger.error(f"Tool selection failed: {e}")
            return {
                "selected_tools": [],
                "last_error": f"Tool selection error: {str(e)}"
            }

    async def extraction_node(self, state: AgentState) -> Dict:
        """Extract entities using selected tools"""
        try:
            self.logger.info("Starting extraction phase")
            
            pending_patches = []
            tool_outputs = {}
            
            # Get extraction tools
            available_tools = self.tool_registry.get_available_tools()
            extraction_tools = [tool for tool in available_tools if "extract" in tool.name]
            
            for tool in extraction_tools:
                try:
                    # Execute extraction tool
                    result = await tool.execute({"text": state["user_goal"]})
                    tool_outputs[tool.name] = result
                    
                    if result.get("success") and result.get("patches"):
                        # Convert patch dicts back to Patch objects
                        for patch_dict in result["patches"]:
                            patch = Patch(**patch_dict)
                            pending_patches.append(patch)
                    
                    self.logger.info(f"Tool {tool.name} extracted {result.get('count', 0)} entities")
                    
                except Exception as e:
                    self.logger.error(f"Tool {tool.name} failed: {e}")
                    tool_outputs[tool.name] = {"success": False, "error": str(e)}
            
            self.logger.info(f"Extraction completed: {len(pending_patches)} patches generated")
            return {
                "pending_patches": pending_patches,
                "tool_outputs": tool_outputs
            }
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return {
                "pending_patches": [],
                "last_error": f"Extraction error: {str(e)}"
            }

    async def validation_node(self, state: AgentState) -> Dict:
        """Validate extracted patches"""
        try:
            self.logger.info("Starting validation phase")
            
            patches = state["pending_patches"]
            if not patches:
                self.logger.warning("No patches to validate")
                return {"last_error": None}

            # Run validation pipeline
            validation_result = await self.validation_pipeline.validate_patches(patches)
            
            if validation_result.success:
                self.logger.info(f"Validation successful: {len(validation_result.validated_patches)} patches validated")
                return {
                    "pending_patches": validation_result.validated_patches,
                    "last_error": None
                }
            else:
                error_msg = f"Validation failed at {validation_result.stage.value}: {', '.join(validation_result.errors)}"
                self.logger.error(error_msg)
                return {
                    "last_error": error_msg,
                    "retry_count": state["retry_count"] + 1,
                    "error_history": state["error_history"] + [error_msg]
                }
                
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                "last_error": f"Validation error: {str(e)}",
                "retry_count": state["retry_count"] + 1,
                "error_history": state["error_history"] + [f"Validation error: {str(e)}"]
            }

    async def execution_node(self, state: AgentState) -> Dict:
        """Apply validated patches to graph store"""
        try:
            self.logger.info("Starting execution phase")
            
            patches = state["pending_patches"]
            if not patches:
                self.logger.warning("No patches to execute")
                return {"applied_operations": []}

            # Apply patches to graph store
            result = self.graph_store.upsert(patches)
            
            if result["success"]:
                self.logger.info(f"Execution successful: {result['applied']} patches applied")
                return {
                    "applied_operations": [{"patches": patches, "result": result}],
                    "last_error": None
                }
            else:
                error_msg = f"Execution failed: {result.get('message', 'Unknown error')}"
                self.logger.error(error_msg)
                return {
                    "last_error": error_msg,
                    "retry_count": state["retry_count"] + 1,
                    "error_history": state["error_history"] + [error_msg]
                }
                
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            return {
                "last_error": f"Execution error: {str(e)}",
                "retry_count": state["retry_count"] + 1,
                "error_history": state["error_history"] + [f"Execution error: {str(e)}"]
            }

    async def evaluation_node(self, state: AgentState) -> Dict:
        """Evaluate execution results and determine next steps"""
        try:
            self.logger.info("Starting evaluation phase")
            
            # Check if we have errors
            if state["last_error"]:
                # Check if we should retry or escalate
                if state["retry_count"] >= 3:
                    self.logger.warning("Max retries reached, escalating")
                    return {
                        "escalated": True,
                        "escalation_reason": "max_retries_reached"
                    }
                else:
                    self.logger.info(f"Retrying (attempt {state['retry_count'] + 1})")
                    return {}  # Continue with retry
            
            # Advance to next step if no errors
            if state["current_step_index"] < len(state["execution_plan"]) - 1:
                self.logger.info("Moving to next step")
                return {
                    "current_step_index": state["current_step_index"] + 1,
                    "retry_count": 0  # Reset retry count for new step
                }
            else:
                self.logger.info("All steps completed successfully")
                return {}  # Move to answer generation
                
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return {
                "last_error": f"Evaluation error: {str(e)}",
                "escalated": True,
                "escalation_reason": "evaluation_error"
            }

    async def answer_generation_node(self, state: AgentState) -> Dict:
        """Generate final response to user"""
        try:
            self.logger.info("Generating final answer")
            
            # Prepare response data
            processing_results = {
                "entities_created": len(state.get("applied_operations", [])),
                "patches_applied": sum(len(op.get("patches", [])) for op in state.get("applied_operations", [])),
                "errors": state.get("error_history", []),
                "escalated": state.get("escalated", False)
            }
            
            # Generate response using LLM
            response = await self.llm_service.generate_text(
                prompt_template=self.prompts.get_answer_generation_prompt(),
                context={
                    "user_goal": state["user_goal"],
                    "processing_results": processing_results
                }
            )
            
            if response.success:
                final_result = {
                    "response": response.content,
                    "success": True,
                    "processing_results": processing_results
                }
            else:
                # Fallback response
                final_result = {
                    "response": f"I've processed your request: '{state['user_goal']}'. "
                              f"Created {processing_results['entities_created']} entities with "
                              f"{processing_results['patches_applied']} operations.",
                    "success": True,
                    "processing_results": processing_results
                }
            
            self.logger.info("Answer generation completed")
            return {"final_result": final_result}
            
        except Exception as e:
            self.logger.error(f"Answer generation failed: {e}")
            return {
                "final_result": {
                    "response": f"I encountered an error while processing your request: {str(e)}",
                    "success": False,
                    "error": str(e)
                }
            }

    def _handle_validation_failure(self, state: AgentState, errors: List[str], stage: str) -> Dict:
        error_message = f"{stage.title()} validation failed: {'; '.join(errors)}"
        return {
            "last_error": error_message,
            "retry_count": state["retry_count"] + 1,
            "error_history": state["error_history"] + [error_message],
        }
