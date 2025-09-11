"""Defines the agent graph for the Puntini backend."""
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from apps.backend.models.domain import Epic, Issue, Project, User
from apps.backend.models.graph import NodeSpec, Patch


class AgentState(TypedDict):
    """Represents the state of our graph."""

    input: str
    extracted_entities: list
    validated_entities: list
    upsert_results: dict
    response: str


def extract(state: AgentState):
    """Extract entities from the input."""
    print("---EXTRACT---")
    text = state["input"]
    entities = []

    # Heuristic-based extraction
    if "create project" in text:
        key_match = re.search(r"key '([^']*)'", text)
        name_match = re.search(r"name '([^']*)'", text)
        if key_match and name_match:
            entities.append(
                Project(key=key_match.group(1), name=name_match.group(1))
            )

    if "create epic" in text:
        key_match = re.search(r"key '([^']*)'", text)
        title_match = re.search(r"title '([^']*)'", text)
        project_key_match = re.search(r"project '([^']*)'", text)
        if key_match and title_match and project_key_match:
            entities.append(
                Epic(
                    key=key_match.group(1),
                    title=title_match.group(1),
                    project_key=project_key_match.group(1),
                )
            )

    if "create issue" in text:
        key_match = re.search(r"key '([^']*)'", text)
        title_match = re.search(r"title '([^']*)'", text)
        if key_match and title_match:
            entities.append(Issue(key=key_match.group(1), title=title_match.group(1)))

    if "create user" in text:
        id_match = re.search(r"id '([^']*)'", text)
        name_match = re.search(r"name '([^']*)'", text)
        if id_match and name_match:
            entities.append(User(user_id=id_match.group(1), name=name_match.group(1)))

    return {"extracted_entities": entities}


def validate(state: AgentState):
    """Validate the extracted entities."""
    print("---VALIDATE---")
    validated_entities = []
    for entity in state["extracted_entities"]:
        if isinstance(entity, (Project, User, Epic, Issue)):
            validated_entities.append(entity)
        else:
            # Here you could add more sophisticated error handling
            print(f"Warning: Invalid entity detected: {entity}")
    return {"validated_entities": validated_entities}


def upsert(state: AgentState):
    """Upsert the validated entities into the graph."""
    print("---UPSERT---")
    patches = []
    for entity in state["validated_entities"]:
        if isinstance(entity, Project):
            node_spec = NodeSpec(
                label="Project", key=entity.key, props=entity.model_dump()
            )
            patches.append(Patch(op="AddNode", node=node_spec))
        elif isinstance(entity, Epic):
            node_spec = NodeSpec(label="Epic", key=entity.key, props=entity.model_dump())
            patches.append(Patch(op="AddNode", node=node_spec))
        elif isinstance(entity, Issue):
            node_spec = NodeSpec(label="Issue", key=entity.key, props=entity.model_dump())
            patches.append(Patch(op="AddNode", node=node_spec))
        elif isinstance(entity, User):
            node_spec = NodeSpec(
                label="User", key=entity.user_id, props=entity.model_dump()
            )
            patches.append(Patch(op="AddNode", node=node_spec))

    # In a real implementation, this would call the GraphStore.
    return {"upsert_results": [p.model_dump() for p in patches]}


def answer(state: AgentState):
    """Generate a final response."""
    print("---ANSWER---")
    num_entities = len(state.get("upsert_results", []))
    if num_entities > 0:
        response = f"Successfully created {num_entities} entities."
    else:
        response = "No entities were created."
    return {"response": response}


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
