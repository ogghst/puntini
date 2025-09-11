# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the project structure, conventions, and key components.

## Project Overview

This project is the backend for the **Puntini Business Improvement Project Management system**. It is a Python-based application built with the **FastAPI** framework.

The core of the application is a sophisticated **AI agent** built using the **`langgraph`** library. This agent is responsible for processing user requests through a stateful workflow that includes planning, tool selection, data extraction, validation, execution, and response generation.

The backend uses a **Neo4j graph database** for data persistence, which is accessed through the `neo4j` library. The agent's workflow is designed to interact with this graph database, enabling complex data relationships and queries.

The project emphasizes code quality and maintainability, with a comprehensive suite of tools for **linting, formatting, and testing**. These include `ruff`, `black`, `isort`, `mypy`, `pylint`, `bandit`, and `pytest`.

## Key Technologies

*   **Backend Framework:** FastAPI
*   **AI Agent:** `langgraph`, `langchain`
*   **Database:** Neo4j
*   **Data Validation:** Pydantic
*   **Testing:** `pytest`, `pytest-cov`
*   **Linting & Formatting:** `ruff`, `black`, `isort`, `mypy`, `pylint`, `bandit`

## Building and Running

The project uses a `Makefile` to provide convenient commands for common development tasks.

### Installation

To install the necessary dependencies, run:

```bash
make install-dev
```

This will install all production and development dependencies, as well as set up pre-commit hooks.

### Running the Server

To run the development server with auto-reload, use the following command:

```bash
make dev
```

The server will be available at `http://localhost:8000`.

### Running Tests

To run the test suite, use the following command:

```bash
make test
```

To run the tests with a coverage report, use:

```bash
make test-cov
```

## Development Conventions

### Code Style

The project follows the **Black** code style, with a line length of 88 characters. **isort** is used to automatically sort imports.

### Linting

The project uses a combination of `ruff`, `flake8`, `pylint`, and `mypy` for linting and static analysis. To run all linting checks, use the following command:

```bash
make lint
```

To automatically fix linting issues, run:

```bash
make lint-fix
```

### Commits

The project uses **pre-commit hooks** to ensure that all code is properly formatted and linted before being committed.

## Project Structure

*   `main.py`: The main entry point for the FastAPI application.
*   `api/`: Contains the API routers and endpoint definitions.
*   `agent/`: Contains the core logic for the AI agent, including the `langgraph` state machine.
*   `graphstore/`: Contains the logic for interacting with the Neo4j graph database.
*   `models/`: Contains the Pydantic data models used throughout the application.
*   `config/`: Contains the application configuration.
*   `tests/`: Contains the test suite.
*   `Makefile`: Provides convenient commands for development tasks.
*   `pyproject.toml`: Contains the project metadata and tool configurations.
*   `requirements.txt`: Lists the project dependencies.
