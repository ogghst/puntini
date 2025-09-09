# Puntini

![puntini](docs/puntini.gif)

Puntini is an AI agent that assists in the creation and management of business improvement projects using Agile and PMI methodologies. It translates natural language prompts and dialogues into entities and relationships on a property graph, complete with validation and audit controls.

## 🌟 Project Scope

Puntini is designed to be a powerful, flexible, and intuitive assistant for project management. It aims to bridge the gap between natural language and structured project management methodologies.

### Key Objectives

- **Granular Control:** Utilizes LangGraph to provide fine-grained control over the project management workflow.
- **Structured Outputs:** Employs Pydantic models to ensure all outputs are structured, validated, and predictable.
- **Idempotent Persistence:** Features an abstract `GraphStore` for idempotent persistence, ensuring data consistency and reliability.
- **User-Friendly Interface:** A FastAPI and React-based user interface for a seamless user experience.
- **End-to-End Traceability:** Provides complete traceability of all actions and changes within the project.

### Core Features (Epics)

- **Project Creation:** Generate a complete project structure, including epics, issues, and user assignments, from a single natural language prompt.
- **Information Retrieval:** Ask questions about your project in natural language and get contextual answers about status, dependencies, risks, and progress.
- **Graph-Based Project Management:** Incrementally build and modify your project's structure using a graph-based approach, with validated Pydantic patches.
- **Prompt-Based Modifications:** Modify the project graph using natural language prompts, with changes applied as idempotent patches.
- **Governance and Audit:** A complete timeline of operations, readable diffs, approval rules, and safe rollbacks for all changes.
- **Collaborative Interface:** A React-based dashboard with a board view for epics and issues, a relationship editor, and a FastAPI API for integrations.

## 🚀 Use Cases

Puntini can be used to solve a variety of real-world project management challenges.

- **Project Kick-off:** A project manager can quickly start a new project by providing a high-level description. Puntini will then create the project structure with epics and user stories.
- **Status Reporting:** A stakeholder can ask "What is the current status of the payment gateway integration?" and Puntini will provide a summary based on the information in the graph.
- **Risk Analysis:** A team member can identify a new risk and add it to the project. They can then ask "What issues are blocked by the 'third-party API outage' risk?"

## 🛠️ Technology Stack

Puntini is built on a modern, robust, and scalable technology stack.

### Backend

- **Framework:** [LangGraph](https://langchain-ai.github.io/langgraph/) for stateful graph orchestration.
- **Orchestration:** A state machine with `Extract→Validate→Upsert→Answer` nodes.
- **Validation:** [Pydantic](https://pydantic-docs.helpmanual.io/) for structured data validation.
- **Database:** An abstract `GraphStore` supporting [Neo4j](https://neo4j.com/) and [NebulaGraph](https://nebula-graph.io/).
- **API:** [FastAPI](https://fastapi.tiangolo.com/) for the REST API.

### Frontend

- **Framework:** [React](https://reactjs.org/) for the user interface.
- **Component Library:** A custom library of reusable UI components.
- **State Management:** Client-side state management for real-time updates.

## 🌱 Potential Improvements

We have a long and exciting roadmap for Puntini. We welcome contributions in any of the following areas:

- **NebulaGraph Integration:** Complete the `GraphStore` adapter for NebulaGraph to achieve full parity with the Neo4j implementation.
- **Advanced UI Features:** Enhance the user interface with features like a relationship editor, an audit log viewer, and mutation approval policies.
- **RAG on Graph:** Implement Retrieval-Augmented Generation (RAG) on the project graph to provide more intelligent and context-aware answers.
- **Intelligent Escalation Policies:** Develop more sophisticated escalation policies for the LangGraph orchestrator.
- **End-to-End Testing:** Expand the test suite with end-to-end tests to ensure the stability and reliability of the entire application.

We are also open to feedback on:

- **LLM/Provider Preference:** We are exploring different LLM providers and structured output modes to optimize for compliance and latency.
- **Mutation Approval Policies:** We are looking for input on the best way to implement mutation approval policies.
- **Deployment Requirements:** We are planning for deployment on both cloud and on-premise environments and would appreciate feedback on scalability and SLOs.

## 🏁 Getting Started

To get started with Puntini, you will need to set up both the backend and the frontend.

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd apps/backend
    ```
2.  **Install the dependencies:**
    ```bash
    make install-dev
    ```
3.  **Run the development server:**
    ```bash
    make dev
    ```

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd apps/frontend
    ```
2.  **Install the dependencies:**
    ```bash
    npm install
    ```
3.  **Run the development server:**
    ```bash
    npm run dev
    ```

## 🤝 Contributing

We welcome contributions from the community! If you would like to contribute to Puntini, please read our [contributing guidelines](AGENTS.md) for more information on how to get started.

## 📄 License

Puntini is licensed under the [MIT License](LICENSE).
