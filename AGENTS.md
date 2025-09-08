## Purpose

The agent assists in creating and managing business improvement projects using Agile and PMI methodologies, translating prompts and dialogues into entities and relationships on a property graph with validation and audit controls. [^12][^11]
**Objectives**: granular flow control with LangGraph, structured Pydantic outputs, idempotent persistence via an abstract GraphStore, a FastAPI+React UI, and end-to-end traceability. [^13][^14]
**Non-objectives**: complete delegation of control to the LLM, mutations without validation, lock-in to a single database or provider, or features beyond the Agile/PMI domain in the first release. [^12][^15]

## Epics

- **Project creation**: from a prompt, generate Project, Epic, Issue, User, and canonical relationships with initial KPIs and minimal domain constraints. [^12][^16]
- **Information request**: QA on the graph with NL→Cypher/nGQL generation and contextual answers about status, dependencies, risks, and progress. [^14][^17]
- **Entity and relationship generation**: incremental extraction with structured outputs and validated Pydantic patches, including key deduplication and normalization. [^16][^18]
- **Graph modification via prompt**: application of typed AddNode/UpdateProps/AddEdge/Delete patches with idempotent MERGE and "speakable" error messages. [^14][^13]
- **Governance and audit**: operation timeline, readable diffs, approval rules, and safe rollbacks for sensitive changes. [^10][^19]
- **Interface and collaboration**: React dashboard, board view for epics/issues, relationship editor, and FastAPI API for integrations. [^19][^20]


## Architecture

- **Framework**: LangGraph as a stateful graph orchestration runtime to ensure plan→act→observe cycles with deterministic conditions and escalations. [^13][^21]
- **Orchestrator**: a state machine with Extract→Validate→Upsert→Answer nodes and policies for progressive context disclosure and intelligent escalation. [^22][^13]
- **Validation**: Pydantic models for nodes and Patches, with structured outputs for model→tool contracts and targeted re-asks on validation failure. [^16][^18]
- **Abstract GraphStore**: a single interface for persistence/query on Neo4j and NebulaGraph with Cypher↔nGQL mapping encapsulated in adapters. [^14][^23]
- **QA on graph**: NL→Cypher/nGQL chains for queries and synthetic reports, maintaining the KG as the authoritative source. [^14][^17]
- **API/UI**: FastAPI for endpoints and JSON contracts, React for the dashboard and interactions with the agent and the graph. [^19][^20]


## Folder Structure

- **/apps/backend**: FastAPI (routers, services, GraphStore adapters, auth, health) with contracts and JSON examples for coding assistants. [^19][^10]
- **/apps/frontend**: React (pages, components, services) for the dashboard, epic/issue board, relationship editor, and agent console. [^19][^20]
- **/apps/backend/agent**: LangGraph workflow, nodes, prompts, tool registry, disclosure/escalation policies, and unit tests. [^11][^13]
- **/apps/backend/graphstore**: interfaces, Neo4jStore, NebulaStore, DDL/migrations, and query/upsert mapping. [^14][^23]
- **/apps/backend/models**: Pydantic models for Project, User, Epic, Issue, and Patch/Spec, versioned for backward compatibility. [^16][^18]
- **/infra**: config, env, compose/k8s, Neo4j/Nebula provisioning, and migration scripts. [^19][^10]

Example tree

```
.
├─ apps/
│  ├─ backend/
│  |  ├─ agent/
│  |  ├─ graphstore/
│  |  └─ models/
│  └─ frontend/
└─ infra/
```


## Workflow

- **Orchestration**: LangGraph coordinates Extract→Validate→Upsert→Answer with conditional edges and persistent state, avoiding context overload and uncontrolled loops. [^13][^22]
- **Progressive disclosure**: provide the LLM with only the minimum context for the step, adding error and historical context on failures, with a final escalation phase. [^22][^24]
- **Structured outputs**: the model returns typed nodes and patches adhering to Pydantic with targeted retries when validation fails. [^16][^18]
- **Persistence**: The GraphStore translates patches into idempotent Cypher/nGQL and returns "speakable" errors with correction suggestions for the LLM. [^14][^23]
- **QA**: for each response, an NL→Cypher/nGQL step can be integrated to enrich it with evidence from the graph and cite paths or counts. [^14][^17]


## Project Plan (Incremental)

- **Phase 0**: repo scaffolding, GraphStore interface, base Pydantic models, LangGraph skeleton, FastAPI hello world, and React shell. [^11][^19]
- **Phase 1 (MVP)**: Extract→Validate→Upsert→Answer flow for Project/Epic/Issue/User, active Neo4j, TODO markdown, and minimal metrics. [^14][^16]
- **Phase 2**: NebulaGraph parity with an nGQL adapter, feature flags, and a QA chain for both backends, plus migrations and parity tests. [^23][^17]
- **Phase 3**: advanced UI (board, relationship editor), audit log/diff viewer, auth, and mutation approval policies. [^19][^20]
- **Phase 4**: RAG on the graph, KPIs, intelligent escalation policies, and E2E tests with production hardening. [^25][^13]


## Progress and TODO

- The TODO list lives in /AGENT_TODO.md in a table format with columns for ID, Phase, Priority (P0–P4), Type ([feat][fix][infra][doc]), Description, and Status, plus a legend for the phases. [^10][^19]
- The agent proposes updates at the end of each turn (additions/completions) and asks for confirmation for scope changes, maintaining an audit of modifications. [^10][^26]

Example

```
| ID | Phase | Priority | Type | Description | Status |
|---|---|---|---|---|---|
| F1-1 | 1 | P1 | feat | Implement the Extract→Validate→Upsert→Answer flow | ⬜️ |
| F1-2 | 1 | P1 | infra | Activate and configure the Neo4j adapter | ⬜️ |
```


## Coding Style

- **Elegant and minimal**: clear interfaces, docstrings for all Pydantic models, pure functions in nodes, injected dependencies, structured logging, and granular tests. [^20][^19]
- **Agent-friendly**: tool docstrings rich with instructions, `Annotated` Pydantic for field semantics, short prompts, and few-shots with positive/negative examples to reduce ambiguity. [^26][^24]
- **Scalable**: separation of orchestration/validation/persistence/QA and schema versioning to evolve without breaking changes. [^19][^16]


## Data Model (Updated Policy)

- **Principle**: each entity inherits from a `BaseEntity` with a unique `id` (UUID4). Relationships are exclusively graph edges, never entity attributes, to ensure semantic clarity, efficient traversal, and portability. [^8][^9]
- **Initial entities (nodes)**: Project, User, Epic, Issue with stable natural keys and minimal properties useful for Agile/PMI. [^16][^12]
- **Canonical relationship catalog**: Project -[HAS_EPIC]-> Epic, Epic -[HAS_ISSUE]-> Issue, Issue -[ASSIGNED_TO]-> User, Issue -[BLOCKS]-> Issue, with unique direction and essential properties. [^8][^27]
- **Reification**: when a relationship requires rich properties or complex historical/cardinality management, introduce an intermediate node (e.g., ASSIGNMENT) and connect it with semantic edges. [^28][^8]
- **Pydantic**: used to validate nodes and typed Patches (AddNode, UpdateProps, AddEdge, Delete), not to encapsulate relationships as key arrays. [^16][^18]
- **Portability**: the GraphStore converts Patches into Cypher (Neo4j) or nGQL (Nebula), maintaining semantics and idempotency via controlled MERGE/INSERT EDGE. [^14][^23]

Pydantic Example

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict

class Project(BaseModel):
    key: str = Field(..., description="Unique project key")
    name: str
    description: Optional[str] = None

class User(BaseModel):
    user_id: str
    name: str

class Epic(BaseModel):
    key: str
    title: str
    project_key: str

class Issue(BaseModel):
    key: str
    title: str
    status: Literal["open","in_progress","done","blocked"] = "open"

class NodeSpec(BaseModel):
    label: Literal["Project","User","Epic","Issue","ASSIGNMENT"]
    key: str
    props: Dict = {}

class EdgeSpec(BaseModel):
    src_label: Literal["Project","Epic","Issue","ASSIGNMENT"]
    src_key: str
    rel: Literal["HAS_EPIC","HAS_ISSUE","ASSIGNED_TO","BLOCKS","HAS_ASSIGNMENT","ASSIGNMENT_OF"]
    dst_label: Literal["Epic","Issue","User","ASSIGNMENT"]
    dst_key: str
    props: Dict = {}

class Patch(BaseModel):
    op: Literal["AddNode","UpdateProps","AddEdge","Delete"]
    node: Optional[NodeSpec] = None
    edge: Optional[EdgeSpec] = None
```

Relationship Guidelines

- **Specific naming and unique direction** for relationships to avoid redundancy and ambiguous queries, favoring clear semantic interpretation. [^8][^27]
- **Properties on the edge** for operational metadata, and reification when the effort exceeds the management complexity threshold. [^28][^8]


## Abstract GraphStore

- **Interface**: upsert(patches: List[Patch]) → result, query_nl(question) → answer, query_graph(query: {cypher|ngql}) → rows, migrations, and health. [^14][^23]
- **Neo4jStore**: Patch→Cypher mapping with MERGE/SET and uniqueness constraints on natural keys, plus an NL→Cypher chain for QA. [^29][^14]
- **NebulaStore**: Patch→nGQL mapping with CREATE TAG/EDGE and INSERT EDGE, plus an NL→nGQL chain for QA with encapsulated differences. [^30][^23]


## FastAPI API

- **Endpoints**: POST /agent/act, POST /graph/patch, GET /graph/query, GET/POST /todo, GET /health, with JSON schemas and examples for coding tools. [^19][^10]
- **Security**: environment variables, API keys or OAuth at different levels, and structured logs with trace IDs for audit and diagnosis. [^19][^20]


## React UI

- **Pages**: Dashboard, Epic/Issue Board, Relationship Editor, Agent Console, TODO, with user-friendly errors and confirmations for mutations. [^20][^19]
- **Patterns**: typed services, query caching, and reusable components for scalability and UX consistency. [^20][^19]


## Prompts and Guardrails

- **System prompt**: roles, objectives, disclosure/escalation policies, security limits, and a style of short, verifiable answers. [^26][^12]
- **Few-shots**: examples of correct/incorrect Patches, "speakable" tool errors and corrections, and typical domain-specific NL→Cypher/nGQL questions. [^26][^14]
- **Decoding**: low temperature for structured phases and higher for explanations, with a re-ask fallback on validation failure. [^24][^16]


## Telemetry and Quality

- **Metrics**: schema compliance, tool success rate, latency per step, QA quality, retry and escalation rate. [^12][^19]
- **Logging**: LLM input/output, applied patches, queries, and errors with turn correlation, maintaining privacy and redacting secrets. [^19][^20]


## Environment Variables

- GRAPH_BACKEND={neo4j|nebula}, NEO4J_URI/USER/PASS, NEBULA_ADDR/PORT/USER/PASS, LLM_API_KEY, FEATURE_FLAGS, LOG_LEVEL, UI_BASE_URL. [^19][^14]


## Notes and Best Practices for AGENTS.md

- Make the purpose, capabilities, limits, repo structure, commands, and examples explicit, so coding assistants can execute and generate code consistently. [^10][^31]
- Keep sections short and operational with acceptance criteria and JSON/code examples, avoiding ambiguity and duplication. [^32][^19]


## Feedback Requested

- Preference for LLM/provider and structured output mode (JSON mode or function schemas) to optimize compliance and latency. [^16][^33]
- Mutation approval policies: thresholds for requiring human confirmation before committing to the graph and required audit levels. [^19][^10]
- Deployment requirements: target cloud/on-prem, scalability, initial SLOs, and integration environment with the graph databases. [^19][^14]


## Coding Style

- **Elegant and minimal**: clear interfaces, docstrings for all Pydantic models, pure functions in nodes, injected dependencies, structured logging, and granular tests. [^20][^19]
- **Agent-friendly**: tool docstrings rich with instructions, `Annotated` Pydantic for field semantics, short prompts, and few-shots with positive/negative examples to reduce ambiguity. [^26][^24]
- **Scalable**: separation of orchestration/validation/persistence/QA and schema versioning to evolve without breaking changes. [^19][^16]


## Data Model (Updated Policy)

- **Principle**: each entity inherits from a `BaseEntity` with a unique `id` (UUID4). Relationships are exclusively graph edges, never entity attributes, to ensure semantic clarity, efficient traversal, and portability. [^8][^9]
- **Initial entities (nodes)**: Project, User, Epic, Issue with stable natural keys and minimal properties useful for Agile/PMI. [^16][^12]
- **Canonical relationship catalog**: Project -[HAS_EPIC]-> Epic, Epic -[HAS_ISSUE]-> Issue, Issue -[ASSIGNED_TO]-> User, Issue -[BLOCKS]-> Issue, with unique direction and essential properties. [^8][^27]
- **Reification**: when a relationship requires rich properties or complex historical/cardinality management, introduce an intermediate node (e.g., ASSIGNMENT) and connect it with semantic edges. [^28][^8]
- **Pydantic**: used to validate nodes and typed Patches (AddNode, UpdateProps, AddEdge, Delete), not to encapsulate relationships as key arrays. [^16][^18]
- **Portability**: the GraphStore converts Patches into Cypher (Neo4j) or nGQL (Nebula), maintaining semantics and idempotency via controlled MERGE/INSERT EDGE. [^14][^23]

Pydantic Example

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict

class Project(BaseModel):
    key: str = Field(..., description="Unique project key")
    name: str
    description: Optional[str] = None

class User(BaseModel):
    user_id: str
    name: str

class Epic(BaseModel):
    key: str
    title: str
    project_key: str

class Issue(BaseModel):
    key: str
    title: str
    status: Literal["open","in_progress","done","blocked"] = "open"

class NodeSpec(BaseModel):
    label: Literal["Project","User","Epic","Issue","ASSIGNMENT"]
    key: str
    props: Dict = {}

class EdgeSpec(BaseModel):
    src_label: Literal["Project","Epic","Issue","ASSIGNMENT"]
    src_key: str
    rel: Literal["HAS_EPIC","HAS_ISSUE","ASSIGNED_TO","BLOCKS","HAS_ASSIGNMENT","ASSIGNMENT_OF"]
    dst_label: Literal["Epic","Issue","User","ASSIGNMENT"]
    dst_key: str
    props: Dict = {}

class Patch(BaseModel):
    op: Literal["AddNode","UpdateProps","AddEdge","Delete"]
    node: Optional[NodeSpec] = None
    edge: Optional[EdgeSpec] = None
```

Relationship Guidelines

- **Specific naming and unique direction** for relationships to avoid redundancy and ambiguous queries, favoring clear semantic interpretation. [^8][^27]
- **Properties on the edge** for operational metadata, and reification when the effort exceeds the management complexity threshold. [^28][^8]


## Abstract GraphStore

- **Interface**: upsert(patches: List[Patch]) → result, query_nl(question) → answer, query_graph(query: {cypher|ngql}) → rows, migrations, and health. [^14][^23]
- **Neo4jStore**: Patch→Cypher mapping with MERGE/SET and uniqueness constraints on natural keys, plus an NL→Cypher chain for QA. [^29][^14]
- **NebulaStore**: Patch→nGQL mapping with CREATE TAG/EDGE and INSERT EDGE, plus an NL→nGQL chain for QA with encapsulated differences. [^30][^23]


## FastAPI API

- **Endpoints**: POST /agent/act, POST /graph/patch, GET /graph/query, GET/POST /todo, GET /health, with JSON schemas and examples for coding tools. [^19][^10]
- **Security**: environment variables, API keys or OAuth at different levels, and structured logs with trace IDs for audit and diagnosis. [^19][^20]


## React UI

- **Pages**: Dashboard, Epic/Issue Board, Relationship Editor, Agent Console, TODO, with user-friendly errors and confirmations for mutations. [^20][^19]
- **Patterns**: typed services, query caching, and reusable components for scalability and UX consistency. [^20][^19]


## Prompts and Guardrails

- **System prompt**: roles, objectives, disclosure/escalation policies, security limits, and a style of short, verifiable answers. [^26][^12]
- **Few-shots**: examples of correct/incorrect Patches, "speakable" tool errors and corrections, and typical domain-specific NL→Cypher/nGQL questions. [^26][^14]
- **Decoding**: low temperature for structured phases and higher for explanations, with a re-ask fallback on validation failure. [^24][^16]


## Telemetry and Quality

- **Metrics**: schema compliance, tool success rate, latency per step, QA quality, retry and escalation rate. [^12][^19]
- **Logging**: LLM input/output, applied patches, queries, and errors with turn correlation, maintaining privacy and redacting secrets. [^19][^20]


## Environment Variables

- GRAPH_BACKEND={neo4j|nebula}, NEO4J_URI/USER/PASS, NEBULA_ADDR/PORT/USER/PASS, LLM_API_KEY, FEATURE_FLAGS, LOG_LEVEL, UI_BASE_URL. [^19][^14]


## Notes and Best Practices for AGENTS.md

- Make the purpose, capabilities, limits, repo structure, commands, and examples explicit, so coding assistants can execute and generate code consistently. [^10][^31]
- Keep sections short and operational with acceptance criteria and JSON/code examples, avoiding ambiguity and duplication. [^32][^19]


## Feedback Requested

- Preference for LLM/provider and structured output mode (JSON mode or function schemas) to optimize compliance and latency. [^16][^33]
- Mutation approval policies: thresholds for requiring human confirmation before committing to the graph and required audit levels. [^19][^10]
- Deployment requirements: target cloud/on-prem, scalability, initial SLOs, and integration environment with the graph databases. [^19][^14]

[^1]: https://langchain-ai.github.io/langgraph/concepts/template_applications/

[^2]: https://github.com/langchain-ai/langgraph/issues/5551

[^3]: https://langchain-ai.github.io/langgraph/agents/agents/

[^4]: https://www.youtube.com/watch?v=mNxAM1ETBvs

[^5]: https://realpython.com/langgraph-python/
[^6]: https://blog.langchain.com/how-to-build-the-ultimate-ai-automation-with-multi-agent-collaboration/

[^7]: https://blog.langchain.com/building-langgraph/

[^8]: https://neo4j.com/graphacademy/training-gdm-40/03-graph-data-modeling-core-principles/

[^9]: https://docs.nebula-graph.io/3.3.0/nebula-studio/quick-start/st-ug-plan-schema/

[^10]: https://github.com/openai/agents.md

[^11]: https://www.langchain.com/langgraph

[^12]: https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf

[^13]: https://langchain-ai.github.io/langgraph/concepts/low_level/

[^14]: https://python.langchain.com/docs/integrations/graphs/neo4j_cypher/

[^15]: https://docs.langchain.com/oss/python/langchain-structured-output

[^16]: https://python.langchain.com/docs/concepts/structured_outputs/

[^17]: https://python.langchain.com/api_reference/community/chains/langchain_community.chains.graph_qa.nebulagraph.NebulaGraphQAChain.html

[^18]: https://python.langchain.com/docs/how_to/structured_output/

[^19]: https://virtuslab.com/blog/backend/providing-library-documentation/

[^20]: https://www.honeycomb.io/blog/how-i-code-with-llms-these-days

[^21]: https://langchain-ai.github.io/langgraph/

[^22]: https://docs.langchain.com/oss/javascript/langgraph/context

[^23]: https://python.langchain.com/docs/integrations/graphs/nebula_graph/

[^24]: https://python.langchain.com/docs/concepts/chat_models/

[^25]: https://microsoft.github.io/graphrag/

[^26]: https://www.anthropic.com/engineering/claude-code-best-practices

[^27]: https://neo4j.com/docs/getting-started/data-modeling/tutorial-data-modeling/

[^28]: https://db-engines.com/de/blog_post/61

[^29]: https://neo4j.com/docs/cypher-manual/current/constraints/managing-constraints/

[^30]: https://docs.nebula-graph.io/3.1.0/3.ngql-guide/11.edge-type-statements/1.create-edge/

[^31]: https://www.infoq.com/news/2025/08/agents-md/

[^32]: https://research.aimultiple.com/agents-md/

[^33]: https://platform.openai.com/docs/guides/structured-outputs