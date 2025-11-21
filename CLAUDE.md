# CLAUDE.md - AI Assistant Guide for OmniBuilder

This document provides essential context for AI assistants working on The-Ultimate-OmniBuilder-Agent-Blueprint project.

## Project Overview

**OmniBuilder** is an autonomous developer, researcher, and executor system designed to:
- Plan, build, code, debug, and manage projects end-to-end
- Operate directly within VS Code (IDE) and Terminal (CLI) environments
- Prioritize autonomy, safety, and deep environmental awareness

### Project Status

**Current State:** Core Implementation Complete
- Full Python implementation with all core modules
- 21 functional modules across 3 architectural layers
- CLI interface with interactive and batch modes
- Ready for testing and enhancement

### License

MIT License (2025) - Open source collaboration enabled

---

## Repository Structure

```
/
├── README.md                    # Project description and vision
├── LICENSE                      # MIT License
├── CLAUDE.md                    # This file - AI assistant guide
├── BLUEPRINT.md                 # Detailed functional specification
├── pyproject.toml               # Python project configuration
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore patterns
└── src/omnibuilder/             # Main source code
    ├── __init__.py              # Package initialization
    ├── agent.py                 # Main agent orchestrator
    ├── cli.py                   # CLI interface
    ├── config.py                # Configuration management
    ├── models.py                # Core data models
    ├── core/                    # Core architectural functions (Part 1)
    │   ├── planner.py           # Goal decomposition & planning
    │   ├── selector.py          # Tool/function selection
    │   ├── reasoning.py         # Core reasoning engine
    │   ├── memory_ltm.py        # Long-term memory manager
    │   ├── memory_stm.py        # Working memory manager
    │   ├── error_handler.py     # Self-correction & error handling
    │   ├── generator.py         # Code & artifact generation
    │   └── formatter.py         # Output formatting
    ├── environment/             # Environment interface functions (Part 2)
    │   ├── codebase.py          # Codebase context provider
    │   ├── terminal.py          # Terminal execution agent
    │   ├── filesystem.py        # File system operations
    │   ├── local_llm.py         # Local LLM integration (Ollama/LM Studio)
    │   ├── ide.py               # VS Code IDE integration
    │   └── safety.py            # Safety prompts & confirmation
    └── tools/                   # External tooling functions (Part 3)
        ├── version_control.py   # Git operations
        ├── web_research.py      # Web search & scraping
        ├── cloud.py             # Cloud & deployment tools
        ├── data.py              # Database & query tools
        ├── communication.py     # Messaging & notifications
        ├── visualization.py     # Diagrams & charts
        └── debugging.py         # Debug & profiling tools
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| CLI Framework | Typer + Rich |
| LLM Clients | Anthropic, OpenAI, Ollama |
| Data Models | Pydantic |
| Async | asyncio, httpx |
| Vector DB | ChromaDB |
| Config | YAML, TOML, dotenv |

---

## Development Workflow

### Getting Started

```bash
# Clone the repository
git clone https://github.com/kimosaa/The-Ultimate-OmniBuilder-Agent-Blueprint
cd The-Ultimate-OmniBuilder-Agent-Blueprint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .
# or
pip install -r requirements.txt

# Initialize OmniBuilder in a project
omnibuilder init

# Run a task
omnibuilder run "Create a hello world script"

# Start interactive chat
omnibuilder chat

# View available tools
omnibuilder tools

# Create an execution plan
omnibuilder plan "Build a REST API"
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `omnibuilder run <goal>` | Execute a goal autonomously |
| `omnibuilder chat` | Start interactive chat session |
| `omnibuilder init` | Initialize config in project |
| `omnibuilder index` | Index codebase for context |
| `omnibuilder plan <goal>` | Create execution plan |
| `omnibuilder tools` | List available tools |

### Configuration

OmniBuilder uses `.omnibuilder/config.yaml` for configuration:

```yaml
llm:
  provider: anthropic  # or openai, ollama, lmstudio
  model: claude-sonnet-4-20250514
  temperature: 0.7
  max_tokens: 4096

safety:
  safe_mode: true
  require_confirmation_high_risk: true
  max_execution_time: 300

memory:
  enable_long_term_memory: true
  max_context_tokens: 100000

tools:
  enable_web_search: true
  enable_git: true
  enable_docker: false
```

Environment variables:
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OPENAI_API_KEY` - OpenAI API key
- `OMNIBUILDER_MODEL` - Override default model

---

## Architecture Overview

### Three-Layer Architecture

1. **Core Functions (Part 1)** - The "Brain"
   - Goal decomposition and planning
   - Tool selection and routing
   - Reasoning and chain-of-thought
   - Memory management (short and long-term)
   - Self-correction and error handling
   - Code and artifact generation
   - Output formatting

2. **Environment Functions (Part 2)** - IDE/CLI Integration
   - Codebase indexing and search
   - Terminal command execution
   - File system operations with safety
   - Local LLM connections
   - VS Code API integration
   - Safety confirmations

3. **External Tools (Part 3)** - API Handlers
   - Version control (Git)
   - Web research
   - Cloud deployment
   - Database operations
   - Communication (email, Slack)
   - Visualization (Mermaid, charts)
   - Debugging and profiling

### Key Design Patterns

- **Async-first**: All I/O operations are async
- **Pydantic models**: Strong typing and validation
- **Risk classification**: Actions categorized by risk level
- **Audit logging**: All sensitive actions logged
- **Graceful degradation**: Fallbacks when tools unavailable

---

## Core Modules Reference

### Agent Orchestrator (`agent.py`)

```python
from omnibuilder import OmniBuilderAgent

agent = OmniBuilderAgent()
await agent.initialize()

# Run a task
result = await agent.run("Create a REST API with FastAPI")

# Chat interaction
response = await agent.chat("How does the codebase handle authentication?")
```

### Planner (`core/planner.py`)

```python
from omnibuilder.core.planner import Planner

planner = Planner()
plan = await planner.create_execution_plan("Build user authentication")
# Returns ExecutionPlan with ordered TaskSteps
```

### Tool Selector (`core/selector.py`)

```python
from omnibuilder.core.selector import ToolSelector

selector = ToolSelector()
tool = await selector.select_tool(context, "run tests")
validation = selector.validate_tool_params(tool, params)
```

### Terminal Agent (`environment/terminal.py`)

```python
from omnibuilder.environment.terminal import TerminalExecutionAgent

terminal = TerminalExecutionAgent(safe_mode=True)
result = await terminal.execute_shell("npm test", timeout=60)
```

### Safety System (`environment/safety.py`)

```python
from omnibuilder.environment.safety import SafetyPrompt, Action

safety = SafetyPrompt()
action = Action(name="git_push", description="Push to main", command="git push")
risk = safety.classify_risk(action)  # Returns RiskLevel
approved = await safety.confirm_action(action)
```

---

## Important Considerations for AI Assistants

### When Working on This Project

1. **Understand the Architecture**: Follow the three-layer pattern (Core → Environment → Tools)

2. **Safety is Non-Negotiable**: All commands must go through the safety system
   - Use `SafetyPrompt.classify_risk()` for risk assessment
   - Require confirmation for high/critical risk actions
   - Log all sensitive operations

3. **Async Throughout**: Use `async/await` for all I/O operations

4. **Type Everything**: Use Pydantic models and type hints

5. **Test Thoroughly**: Cover edge cases and failure scenarios

### Key Files to Understand

| File | Purpose |
|------|---------|
| `agent.py` | Main orchestrator - understand this first |
| `models.py` | All data types and enums |
| `config.py` | Configuration loading and defaults |
| `core/planner.py` | Task decomposition logic |
| `core/selector.py` | Tool routing logic |
| `environment/safety.py` | Risk classification |

### Adding New Features

1. **New Tool**: Add to `tools/` directory, register in `ToolSelector`
2. **New Core Function**: Add to `core/`, wire into `agent.py`
3. **New Environment Integration**: Add to `environment/`

### Risk Levels

| Level | Examples | Action Required |
|-------|----------|-----------------|
| Critical | `rm -rf /`, `DROP DATABASE` | Always confirm + reason |
| High | `git push`, `sudo` | Confirm required |
| Medium | `git commit`, `pip install` | Warn user |
| Low | `read file`, `search code` | Auto-approve |

---

## Development Priorities

### Completed ✓
- [x] Core architecture implementation
- [x] All 8 core functions
- [x] All 6 environment functions
- [x] All 7 tool categories
- [x] CLI interface
- [x] Configuration system

### Next Steps
- [ ] Add comprehensive test suite
- [ ] Implement VS Code extension
- [ ] Add more LLM provider support
- [ ] Enhance memory with vector embeddings
- [ ] Create example projects
- [ ] Add CI/CD pipeline
- [ ] Performance optimization
- [ ] Documentation site

---

## Quick Reference

| Aspect | Status/Info |
|--------|-------------|
| Project Stage | Core Implementation Complete |
| License | MIT |
| Language | Python 3.10+ |
| CLI Tool | `omnibuilder` or `ob` |
| Main Entry | `src/omnibuilder/cli.py` |
| Config File | `.omnibuilder/config.yaml` |
| Tests | Pending |
| CI/CD | Pending |

---

## Running the Agent

```bash
# Quick start
pip install -e .
export ANTHROPIC_API_KEY=your-key
omnibuilder chat

# Or run a specific task
omnibuilder run "Analyze this codebase and create a summary"
```

---

*Last Updated: 2025-11-20*
