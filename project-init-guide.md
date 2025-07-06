# Python Project Structure Guide

This guide outlines how to create a professional Python library project structure for `MyPythonLib` - designed for PyPI distribution with modern development practices.

## Project Philosophy

This structure emphasizes:
- **Separation of Concerns**: Clear organization with distinct purposes for each directory
- **Modern Standards**: Following current Python packaging best practices
- **AI Collaboration**: Structured approach for working with AI assistants
- **Professional Workflow**: Tools and processes for quality development
- **Future-Proof**: Designed to scale and evolve with changing requirements

## Directory Structure Overview

```
MyPythonLib/
├── .github/workflows/          # Automation workflows
├── src/mypythonlib/           # Main package code (src layout)
├── scripts/                   # Command-line interface tools
├── tests/                     # Test suite
├── docs/                      # Documentation source
├── context/                   # AI assistant workspace
│   ├── design/               # API and technical design docs
│   ├── plans/                # Implementation roadmaps
│   ├── hints/                # Programming guides and tutorials
│   ├── summaries/            # Project knowledge base
│   ├── tasks/                # Human-defined task requests
│   ├── logs/                 # Development history logs
│   ├── refcode/              # Reference implementations
│   └── tools/                # Custom development utilities
├── tmp/                      # Temporary working files
└── [configuration files]     # Project setup and tooling
```

## Core Components

### Source Code Organization

**src/mypythonlib/** - Main Package
- Contains the core library functionality
- Uses "src layout" for better testing isolation
- Includes package initialization and module definitions
- Houses the primary API that users will import

**scripts/** - Command Line Tools
- Entry points for terminal commands
- Provides CLI interface to library functionality
- Designed for both user convenience and automation
- Configured as console scripts in packaging

### Quality and Testing

**tests/** - Test Suite
- Comprehensive testing for all functionality
- Organized to mirror source code structure
- Includes unit tests, integration tests, and end-to-end tests
- Configured with modern testing frameworks and coverage tools

### Documentation and Communication

**docs/** - Documentation Source
- User-facing documentation written in Markdown
- Built with MkDocs Material for professional presentation
- Automatically deployed to GitHub Pages
- Includes installation guides, API reference, and examples

### AI Collaboration Framework

**context/** - AI Assistant Workspace
This directory enables effective collaboration with AI coding assistants:

**design/** - Technical Design Documents
- API specifications and interface definitions
- System architecture and component relationships
- Technical decision rationales and trade-offs
- Design patterns and implementation guidelines

**plans/** - Implementation Roadmaps
- Feature development timelines and milestones
- Task breakdowns and dependency mappings
- Project phases and deliverable definitions
- Resource planning and risk assessments

**hints/** - Development Knowledge Base
- Programming tutorials and best practices
- Technology-specific guides and patterns
- Common problem solutions and workarounds
- Reference materials for quick consultation

**summaries/** - Project Experience Repository
- Lessons learned from development challenges
- Architecture evolution and decision history
- Performance optimization discoveries
- Integration patterns and solutions

**tasks/** - Human-AI Task Coordination
- Specific development requests from humans
- Task definitions with clear requirements
- Progress tracking and completion criteria
- Communication bridge between humans and AI

**logs/** - Development History
- Session logs for continuity between AI interactions
- Decision-making processes and outcomes
- Debugging sessions and solution paths
- Project evolution timeline

**refcode/** - Reference Implementations
- Example code from similar projects
- Library usage patterns and integration examples
- Best practice demonstrations
- External code repositories as learning resources

**tools/** - Custom Development Utilities
- Project-specific automation scripts
- Code generation and analysis tools
- Development workflow enhancers
- Reusable solutions for common tasks

### Project Configuration

**Root Level Files:**
- **pyproject.toml** - Python packaging configuration with dependencies and metadata
- **pixi.toml** - Environment management and development task definitions
- **mkdocs.yml** - Documentation build configuration
- **README.md** - Primary project introduction and usage guide
- **CLAUDE.md** - AI assistant guidance and project context
- **LICENSE** - Legal terms for code usage and distribution
- **.gitignore** - Version control exclusion patterns

### Automation and Deployment

**.github/workflows/** - CI/CD Automation
- Documentation deployment to GitHub Pages
- Automated testing and quality checks
- Package building and release processes
- Integration with external services

## Development Workflow

### Environment Setup
Projects use Pixi for reproducible development environments, providing consistent dependency management across different machines and operating systems.

### Code Quality
Automated tools ensure consistent code style, type safety, and testing coverage. This includes linting, formatting, and static analysis integrated into the development workflow.

### Documentation Strategy
Documentation is treated as code - written in Markdown, version controlled, and automatically deployed. This ensures documentation stays current with code changes.

### AI Collaboration Model
The context directory structure facilitates effective human-AI collaboration by providing organized spaces for different types of project information and communication.

## Setup Process

### Initial Creation
1. Create project directory structure
2. Initialize git repository with main branch
3. Set up core configuration files
4. Create initial Python package structure
5. Configure development environment with Pixi

### GitHub Integration
1. Create remote repository on GitHub
2. Configure GitHub Pages for documentation
3. Set up automated workflows for deployment
4. Enable issue tracking and discussions

### Development Environment
1. Install Pixi environment manager
2. Initialize project dependencies
3. Configure development tools and workflows
4. Set up testing and quality assurance tools

## Key Principles

### Maintainability
- Clear separation between different types of content
- Consistent naming conventions and organization
- Documentation for all major components and decisions

### Scalability
- Structure supports growth from simple library to complex project
- Modular organization allows independent development of components
- Flexible configuration supports different deployment scenarios

### Collaboration
- AI-friendly organization with clear context and history
- Human-readable documentation and guides
- Version-controlled communication and decision tracking

### Professional Standards
- Follows modern Python packaging best practices
- Includes comprehensive testing and quality assurance
- Professional documentation and presentation
- Automated deployment and release processes

This structure provides a solid foundation for any Python library project, emphasizing clarity, maintainability, and effective collaboration between human developers and AI assistants.