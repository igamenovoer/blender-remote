# Tests

This directory contains the test suite for the blender-remote project.

## Purpose

Tests ensure:
- Remote control library functions correctly
- Communication protocols work as expected
- CLI tools behave properly
- Add-ons integrate correctly with Blender
- Error handling works in various scenarios

## Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for component interactions
├── test_addon/        # Tests for Blender add-on functionality
├── test_remote/       # Tests for remote control library
├── test_cli/          # Tests for CLI scripts
└── conftest.py        # pytest configuration and fixtures
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_remote/test_connection.py

# Run with coverage
pytest --cov=blender_remote tests/

# Run only unit tests
pytest tests/unit/
```

## Testing Challenges

Testing Blender-related code requires special consideration:
- Add-on tests may need a running Blender instance
- Some tests might require mocking Blender's Python API
- Integration tests need both client and server components running