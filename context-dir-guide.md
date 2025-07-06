# Context Directory Specification

This specification defines a standardized context directory structure for AI-assisted software development projects.

## Overview

The `context/` directory provides an organized workspace for AI coding assistants, enabling effective collaboration between human developers and AI systems. This structure maintains project knowledge, facilitates continuity across sessions, and provides reference materials for consistent development.

## Directory Structure Specification

```
context/
├── design/         # API and technical design documentation
├── plans/          # Implementation roadmaps and project planning
├── hints/          # Programming guides and development tutorials
├── summaries/      # Project knowledge base and experience repository
├── tasks/          # Human-defined task requests and specifications
├── logs/           # Development history and session continuity
├── refcode/        # Reference implementations and example code
├── tools/          # Custom development utilities and scripts
└── README.md       # Context directory overview and usage guide
```

## Subdirectory Specifications

### design/
**Purpose**: Store technical design documents and API specifications before implementation begins.

**Recommended Usage**:
This directory typically contains design documents that outline how systems should work before implementation. Common usage patterns include API interface specifications, system architecture diagrams, technical decision documentation with rationales, data models and schema definitions, protocol specifications, and security considerations. Projects might use this space to document constraints, trade-offs, and future extensibility plans. The actual content and organization depends on the project's specific design workflow and documentation needs.

### plans/
**Purpose**: Contain implementation roadmaps, project planning, and development coordination.

**Recommended Usage**:
This directory commonly holds planning documents that organize development work over time. Projects often store feature development plans with task breakdowns, sprint planning and milestone definitions, resource allocation estimates, risk assessments, and release planning schedules. Teams might use this space for coordination workflows, timeline tracking, and scope management. The planning approach and documentation style can vary based on project methodology, team size, and organizational preferences.

### hints/
**Purpose**: Provide programming tutorials, development guides, and best practice documentation.

**Recommended Usage**:
This directory serves as a knowledge base for development guidance and solutions. Projects commonly store technology-specific tutorials, development best practices, troubleshooting guides, tool usage instructions, and framework-specific patterns. Teams might document recurring solutions, performance optimization techniques, and quick reference materials. The content could include code examples, workflow tips, and practical demonstrations. What goes here depends on the team's learning needs and the technologies being used.

### summaries/
**Purpose**: Maintain project experience repository and knowledge base.

**Recommended Usage**:
This directory captures accumulated project wisdom and experience. Teams often document lessons learned from development challenges, architecture evolution histories, performance optimization discoveries, and successful integration patterns. Projects might store retrospectives, technology evaluations, and institutional knowledge that helps preserve context across team changes. The format and depth of summaries can vary from brief notes to detailed case studies, depending on what proves most valuable for the team.

### tasks/
**Purpose**: Coordinate specific development requests between humans and AI assistants.

**Recommended Usage**:
This directory facilitates communication between human developers and AI assistants about specific work items. Common content includes development task specifications, feature requirements, bug reports, enhancement requests, research assignments, and maintenance tasks. Projects might structure these with acceptance criteria, priority levels, and links to related documentation. The organization could range from simple task lists to detailed specifications, depending on project complexity and collaboration needs.

### logs/
**Purpose**: Maintain development history and session continuity for AI assistants.

**Recommended Usage**:
This directory preserves context and history for ongoing AI-assisted development. Projects commonly store AI assistant session summaries, decision-making processes, debugging session outcomes, and project evolution timelines. Teams might document significant development milestones, learning progressions, and context information that helps maintain continuity across multiple sessions. The logging approach can vary from detailed transcripts to high-level summaries, depending on what provides the most value for maintaining project context.

### refcode/
**Purpose**: Store reference implementations and example code from external sources.

**Recommended Usage**:
This directory holds external code examples and reference implementations that inform project development. Common content includes example implementations from similar projects, library usage patterns, best practice demonstrations, and code snippets for common operations. Projects might organize content using subdirectories for different technologies, include git submodules for complete repositories, or store framework-specific patterns. Teams should maintain clear attribution for external sources and document relevance to current project needs while respecting licensing requirements.

### tools/
**Purpose**: House custom development utilities and project-specific automation scripts.

**Recommended Usage**:
This directory contains project-specific utilities and automation scripts that support development workflows. Common content includes code generation tools, build and deployment automation, data processing utilities, testing helpers, and documentation generators. Projects might organize tools by functionality and include usage documentation for each utility. The tools can range from simple scripts to complex automation systems, depending on project needs and team preferences. Teams often share useful tools across similar projects while maintaining them as requirements evolve.

## Implementation Requirements

### Mandatory Files

Each context directory MUST include:
1. **README.md** - Overview of the context directory structure and usage guidelines
2. **{subdirectory}/README.md** - Purpose documentation for each subdirectory explaining what it is for and what content it contains

### Content Standards

All documentation MUST follow these standards:
- Use Markdown format for consistency and readability
- Include clear purpose statements and usage instructions
- Provide examples where applicable
- Keep content current with project evolution
- Update README.md files to reflect actual content as directories are populated

### Access Patterns

AI assistants SHOULD:
1. Check relevant subdirectories when starting new tasks
2. Reference existing solutions before creating new implementations
3. Add new learnings and discoveries to appropriate locations
4. Update logs and summaries to maintain project continuity
5. Use the context directory to understand project history and patterns

### Maintenance Requirements

Project teams MUST:
1. Regularly review and update context directory content
2. Remove outdated or irrelevant information
3. Ensure new team members understand the context directory structure
4. Integrate context directory usage into development workflows
5. Maintain clear documentation for all custom tools and utilities

## Integration with Development Workflow

### Project Initialization
1. Create context directory structure with all specified subdirectories
2. Add README.md files to each subdirectory explaining its purpose
3. Include context directory in project documentation and onboarding materials

### Development Process
1. Consult relevant context subdirectories before starting new work
2. Document design decisions and technical choices in design/
3. Create implementation plans in plans/ for complex features
4. Record development sessions and outcomes in logs/
5. Add reusable solutions and patterns to hints/ and summaries/

### AI Assistant Integration
1. Provide context directory overview to AI assistants at project start
2. Direct AI assistants to check relevant subdirectories for existing solutions
3. Encourage AI assistants to contribute learnings back to the context directory
4. Use context directory to maintain continuity across AI assistant sessions

## Benefits and Outcomes

This specification provides:
- **Consistency**: Standardized structure across projects and teams
- **Continuity**: Preserved knowledge and context across development sessions
- **Efficiency**: Reduced duplication through shared knowledge and solutions
- **Quality**: Better decision-making through documented experience and best practices
- **Collaboration**: Enhanced human-AI collaboration through organized information sharing

## Version and Evolution

This specification should be versioned and updated as development practices evolve. Projects implementing this structure should:
- Track which version of the specification they follow
- Migrate to newer versions when beneficial
- Contribute improvements back to the specification
- Adapt the structure to project-specific needs while maintaining core principles

## Compliance and Adoption

Projects claiming compliance with this specification MUST:
- Implement all mandatory subdirectories and README.md files
- Follow the documented content standards
- Maintain the directory structure according to usage requirements
- Provide training or documentation for team members on context directory usage

This specification serves as a foundation for effective AI-assisted development workflows and can be adapted to specific project needs while maintaining consistency and interoperability across projects.