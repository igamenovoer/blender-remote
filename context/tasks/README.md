# Tasks

This directory contains task definitions and prompts from humans for AI coding assistants.

## Purpose

- Store specific task requests and requirements
- Maintain history of completed tasks
- Organize complex multi-part projects
- Track task dependencies and relationships

## Organization

Each task should have its own subdirectory:
```
tasks/
├── task_001_initial_setup/
│   ├── prompt.md          # Original task description
│   ├── requirements.md    # Detailed requirements
│   ├── progress.md        # Implementation progress
│   └── solution.md        # Final solution summary
├── task_002_mcp_integration/
└── task_003_cli_tools/
```

## Task Lifecycle

1. **Definition**: Create subdirectory with prompt.md
2. **Analysis**: Document requirements and approach
3. **Implementation**: Track progress and decisions
4. **Completion**: Summarize solution and learnings

## Status Tracking

Each task document should include a status section that clearly states:
- **Created**: When the task was originally created (date)
- **Status**: Current state (pending, in-progress, completed)
- **Progress Summary**: Brief description of what has been accomplished

This enables easy tracking of task progress and helps maintain context across development sessions.

## Naming Convention

- Use sequential numbering: task_XXX_description
- Keep descriptions short but meaningful
- Group related tasks with similar prefixes

## Cross-References

Tasks may reference:
- Solutions in ../summaries/
- Code examples in ../refcode/
- Tools developed in ../tools/
- Implementation logs in ../logs/