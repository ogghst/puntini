from typing import TypedDict

from langgraph.graph import END, StateGraph


# The state of our graph
class AgentState(TypedDict):
    input: str
    extracted_entities: list
    validated_entities: list
    upsert_results: dict
    response: str

def extract(state: AgentState):
    """
    Placeholder for the entity extraction node.
    """
    print("---EXTRACT---")
    # In a real implementation, this would call an LLM to extract entities.
    return {"extracted_entities": ["entity1", "entity2"]}

def validate(state: AgentState):
    """
    Placeholder for the entity validation node.
    """
    print("---VALIDATE---")
    # In a real implementation, this would use Pydantic models to validate.
    return {"validated_entities": state["extracted_entities"]}

def upsert(state: AgentState):
    """
    Placeholder for the graph upsert node.
    """
    print("---UPSERT---")
    # In a real implementation, this would call the GraphStore.
    return {"upsert_results": {"success": True}}

def answer(state: AgentState):
    """
    Placeholder for the final response generation node.
    """
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

# You can uncomment the following lines to visualize the graph
# from IPython.display import Image, display
# try:
#     display(Image(app.get_graph(xray=True).draw_mermaid_png()))
# except:
#     pass
