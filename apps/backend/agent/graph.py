"""Defines the agent graph for the Puntini backend."""
from typing import TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """Represents the state of our graph."""

    input: str
    extracted_entities: list
    validated_entities: list
    upsert_results: dict
    response: str


def extract(_state: AgentState):
    """Extract entities from the input."""
    print("---EXTRACT---")
    # In a real implementation, this would call an LLM to extract entities.
    return {"extracted_entities": ["entity1", "entity2"]}


def validate(state: AgentState):
    """Validate the extracted entities."""
    print("---VALIDATE---")
    # In a real implementation, this would use Pydantic models to validate.
    return {"validated_entities": state["extracted_entities"]}


def upsert(_state: AgentState):
    """Upsert the validated entities into the graph."""
    print("---UPSERT---")
    # In a real implementation, this would call the GraphStore.
    return {"upsert_results": {"success": True}}


def answer(_state: AgentState):
    """Generate a final response."""
    print("---ANSWER---")
    # In a real implementation, this would generate a natural language response.
    return {"response": "Graph has been updated successfully."}


# Define the workflow
workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("extract", extract)
workflow.add_node("validate", validate)
workflow.add_node("upsert", upsert)
workflow.add_node("answer", answer)

# Build the graph
workflow.set_entry_point("extract")
workflow.add_edge("extract", "validate")
workflow.add_edge("validate", "upsert")
workflow.add_edge("upsert", "answer")
workflow.add_edge("answer", END)

# Compile the app
app = workflow.compile()
