# CLAUDE.md - AI Assistant Guide for OmniBuilder

This document provides essential context for AI assistants working on The-Ultimate-OmniBuilder-Agent-Blueprint project.

## Project Overview

**OmniBuilder** is an autonomous developer, researcher, and executor system designed to:
- Plan, build, code, debug, and manage projects end-to-end
- Operate directly within VS Code (IDE) and Terminal (CLI) environments
- Prioritize autonomy, safety, and deep environmental awareness

### Project Status

**Current State:** Blueprint/Initial Stage
- Repository contains only foundational files (README.md, LICENSE)
- No source code, configuration, or infrastructure implemented yet
- Architecture and technology stack decisions pending

### License

MIT License (2025) - Open source collaboration enabled

---

## Repository Structure

### Current Structure
```
/
├── README.md           # Project description and vision
├── LICENSE             # MIT License
└── CLAUDE.md           # This file - AI assistant guide
```

### Expected Future Structure
```
/
├── src/                    # Main source code
│   ├── core/              # Core agent functionality
│   ├── planning/          # Task planning and decomposition
│   ├── execution/         # Code execution and management
│   ├── safety/            # Safety checks and guardrails
│   └── integration/       # IDE/CLI integration modules
├── tests/                  # Test suites
├── docs/                   # Documentation
├── config/                 # Configuration files
├── scripts/               # Build and utility scripts
├── .github/               # CI/CD workflows
└── examples/              # Usage examples
```

---

## Development Guidelines

### Core Design Principles

1. **Autonomy First**: Design components to operate independently with minimal user intervention
2. **Safety by Design**: Implement guardrails and validation at every decision point
3. **Environmental Awareness**: Deep integration with development tools and context
4. **Modularity**: Build loosely coupled, highly cohesive components
5. **Transparency**: Log decisions and actions for auditability

### Code Conventions

When implementing code for this project:

#### General
- Write clear, self-documenting code with meaningful names
- Include comprehensive docstrings/comments for complex logic
- Follow the principle of least surprise
- Keep functions focused and single-purpose

#### Error Handling
- Implement robust error handling with informative messages
- Never silently fail - always log and handle errors appropriately
- Design for graceful degradation

#### Security
- Validate all inputs, especially from external sources
- Implement proper sandboxing for code execution
- Follow principle of least privilege
- Never execute arbitrary code without safety checks

#### Testing
- Write tests for all new functionality
- Aim for high test coverage on critical paths
- Include both unit tests and integration tests
- Test edge cases and failure scenarios

---

## Key Architectural Considerations

### Agent Architecture

OmniBuilder should implement:

1. **Planning Module**
   - Task decomposition
   - Dependency analysis
   - Resource estimation
   - Risk assessment

2. **Execution Engine**
   - Safe code execution
   - Progress tracking
   - Rollback capabilities
   - Resource management

3. **Safety System**
   - Input validation
   - Output verification
   - Sandboxed execution
   - Permission management

4. **Integration Layer**
   - VS Code API integration
   - CLI command execution
   - File system operations
   - Version control integration

### Technology Stack Considerations

When selecting technologies, prioritize:
- Type safety and static analysis
- Cross-platform compatibility
- Strong ecosystem and community
- Security-focused libraries
- Performance for real-time operations

---

## Development Workflow

### Getting Started

Once implementation begins, the workflow should include:

```bash
# Clone the repository
git clone <repository-url>
cd The-Ultimate-OmniBuilder-Agent-Blueprint

# Install dependencies (once configured)
# npm install / pip install / cargo build

# Run tests
# npm test / pytest / cargo test

# Run linting
# npm run lint / pylint / cargo clippy

# Start development server/environment
# npm run dev / python main.py
```

### Git Workflow

1. **Branch Naming**: Use descriptive branch names
   - `feature/` for new features
   - `fix/` for bug fixes
   - `docs/` for documentation
   - `refactor/` for code improvements

2. **Commit Messages**: Use clear, descriptive commit messages
   - Start with a verb (Add, Fix, Update, Refactor)
   - Keep first line under 72 characters
   - Reference issues when applicable

3. **Pull Requests**: Include description of changes and testing performed

---

## Important Considerations for AI Assistants

### When Working on This Project

1. **Understand the Vision**: OmniBuilder aims to be a fully autonomous development agent - keep this goal central to all decisions

2. **Safety is Non-Negotiable**: Any code that executes user commands or modifies files MUST have safety checks

3. **Document Everything**: This is a complex system - thorough documentation is essential

4. **Think Modularly**: Design components that can be tested and updated independently

5. **Consider Edge Cases**: Autonomous systems must handle unexpected situations gracefully

### Common Tasks

#### Adding New Modules
1. Create module in appropriate `src/` subdirectory
2. Add comprehensive tests in `tests/`
3. Update documentation
4. Ensure integration with existing components

#### Implementing Safety Features
1. Identify all potential risks
2. Design validation and verification steps
3. Implement sandboxing where needed
4. Add logging for audit trails
5. Test failure modes explicitly

#### Integrating with IDE/CLI
1. Use official APIs where available
2. Handle permission requirements
3. Implement graceful fallbacks
4. Test across different environments

---

## Future Development Priorities

### Phase 1: Foundation
- [ ] Define technology stack
- [ ] Set up project structure
- [ ] Implement core configuration
- [ ] Create CI/CD pipeline
- [ ] Establish testing infrastructure

### Phase 2: Core Agent
- [ ] Implement planning module
- [ ] Build execution engine
- [ ] Create safety system
- [ ] Develop integration layer

### Phase 3: Integration
- [ ] VS Code extension
- [ ] CLI interface
- [ ] API endpoints
- [ ] Plugin system

### Phase 4: Enhancement
- [ ] Advanced planning algorithms
- [ ] Learning and optimization
- [ ] Extended tool integrations
- [ ] Performance optimization

---

## Resources and References

### Related Concepts
- Autonomous AI agents
- IDE extension development
- Safe code execution
- Task planning and decomposition

### Key Files to Understand
- `README.md` - Project vision and goals
- `LICENSE` - Usage rights and restrictions
- Future: Architecture documentation, API specs

---

## Contributing

When contributing to OmniBuilder:

1. Review existing code and documentation
2. Follow established conventions
3. Write tests for all changes
4. Update documentation as needed
5. Submit clear, focused pull requests

---

## Quick Reference

| Aspect | Status/Info |
|--------|-------------|
| Project Stage | Blueprint/Initial |
| License | MIT |
| Main Branch | `main` |
| Language | TBD |
| Framework | TBD |
| CI/CD | Not configured |
| Tests | Not configured |

---

*Last Updated: 2025-11-20*
