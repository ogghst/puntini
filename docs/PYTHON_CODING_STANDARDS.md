# Coding standards and best practices for all backend development.

## Code Structure & Organization

Use clear, descriptive variable and function names that express intent
Follow PEP 8 style guidelines for consistent formatting
Organize code into modules and packages with logical separation of concerns
Keep functions small and focused on a single responsibility

## Error Handling & Validation

Use specific exception types rather than broad except: clauses
Validate inputs early and provide meaningful error messages
Implement proper logging instead of relying on print statements
Handle edge cases explicitly rather than assuming happy path scenarios

## Type Safety & Documentation

Add type hints to function signatures and complex variables
Write clear docstrings for modules, classes, and functions
Use dataclasses or Pydantic models for structured data
Document complex business logic and non-obvious implementation choices

## Flexibility & Maintainability

Avoid hardcoded values by using configuration files or environment variables
Design with dependency injection to make components testable and swappable
Use abstract base classes or protocols to define clear interfaces
Prefer composition over inheritance for complex relationships

## Performance & Resource Management

Use context managers (with statements) for resource handling
Choose appropriate data structures for your use case
Profile code before optimizing and focus on actual bottlenecks
Consider memory usage patterns, especially with large datasets

## Agent Development Coding Style

- **Elegant and minimal**: clear interfaces, docstrings for all Pydantic models, pure functions in nodes, injected dependencies, structured logging, and granular tests. 
- **Agent-friendly**: tool docstrings rich with instructions, `Annotated` Pydantic for field semantics, short prompts, and few-shots with positive/negative examples to reduce ambiguity. 
- **Scalable**: separation of orchestration/validation/persistence/QA and schema versioning to evolve without breaking changes. 
- **Test-driven**: comprehensive unit tests with proper fixtures, test isolation, and coverage for all public methods and properties. 

### Testing Guidelines

- **Test Structure**: Each module should have a corresponding test file in `/apps/backend/tests/`
- **Fixtures**: Use pytest fixtures for test data setup and teardown, including singleton resets
- **Isolation**: Ensure tests don't depend on each other by resetting global state between tests
- **Coverage**: Aim for 100% test coverage of public methods and critical paths
- **Mocking**: Use `unittest.mock` for external dependencies and side effects
- **Naming**: Test functions should be descriptive and follow `test_<functionality>_<scenario>` pattern