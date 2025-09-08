# Code Structure & Organization

Use clear, descriptive variable and function names that express intent
Follow PEP 8 style guidelines for consistent formatting
Organize code into modules and packages with logical separation of concerns
Keep functions small and focused on a single responsibility

# Error Handling & Validation

Use specific exception types rather than broad except: clauses
Validate inputs early and provide meaningful error messages
Implement proper logging instead of relying on print statements
Handle edge cases explicitly rather than assuming happy path scenarios

# Type Safety & Documentation

Add type hints to function signatures and complex variables
Write clear docstrings for modules, classes, and functions
Use dataclasses or Pydantic models for structured data
Document complex business logic and non-obvious implementation choices

# Testing & Quality Assurance

Write unit tests for critical functions and edge cases
Use tools like pytest for testing and coverage analysis
Implement automated code formatting (black, autopep8) and linting (pylint, flake8)
Set up pre-commit hooks to catch issues early

# Flexibility & Maintainability

Avoid hardcoded values by using configuration files or environment variables
Design with dependency injection to make components testable and swappable
Use abstract base classes or protocols to define clear interfaces
Prefer composition over inheritance for complex relationships

# Performance & Resource Management

Use context managers (with statements) for resource handling
Choose appropriate data structures for your use case
Profile code before optimizing and focus on actual bottlenecks
Consider memory usage patterns, especially with large datasets
