# Pathfinder

AI-driven architecture management using **Structurizr** and the **C4 model**. Install into any project to give Claude Code a structured understanding of your system — visualized, documented, and maintained through agents and skills.

## How it works

Pathfinder adds **two agents** and **two skills** to your project. The agents manage architecture — one for initial discovery, one for ongoing design. The skills provide focused capabilities that agents and users invoke. All model operations go through the **Structurizr MCP Server**; the **Structurizr Server** provides visualization at `localhost:8080`.

```
Flow 1: Init
  User starts Init Agent in fresh context
    → Scans codebase → Builds C4 model via MCP → Maps all code → Visual review

Flow 2: Design
  User provides business requirement (+ specs, mocks, etc.)
    → Architect Agent → Context skill extracts relevant slice
    → Explore alternatives → Before/after visualization → Update model
    → Produce implementation spec
```

### Agents

| Agent | What it does |
|-------|-------------|
| **Init Agent** | Scans an existing codebase, builds the complete C4 model + documentation, maps every source file to a component |
| **System Architect** | Takes business requirements, extracts architectural context, explores alternatives, produces implementation specs |

### Skills

| Skill | What it does |
|-------|-------------|
| **pathfinder-context** | Subagent that reads the full workspace and returns only the relevant architectural slice |
| **pathfinder-review** | Interactive review: walks through each C4 level with the user, collects corrections, iterates |

## Installation

Requires **Python 3.12+** and **Docker**.

```bash
pip install git+https://github.com/popescualextraian/pathfinder-plugin.git
```

## Setting up a project

```bash
# 1. Install skills, agents, and MCP config into your project
pathfinder install

# 2. Initialize the architecture directory
pathfinder init --name my-project

# 3. Start Structurizr Server + MCP
pathfinder start

# 4. (Recommended) Run Claude /init for codebase context, then start fresh session

# 5. Invoke the Init Agent to build the architecture model
```

### What gets installed

```
your-project/
  .claude/
    skills/
      pathfinder-context/SKILL.md
      pathfinder-review/SKILL.md
    agents/
      init-agent.md
      system-architect.md
    settings.local.json              # MCP server config added
  .pathfinder/                       # Created by pathfinder init
    workspace.dsl                    # Structurizr DSL (source of truth)
    config.yaml                      # Project config
    practices.md                     # Architectural best practices (customize this)
```

## Architecture model

The model uses the **C4 standard** (System Context → Container → Component) stored as **Structurizr DSL**:

- **Workspace** — managed by Structurizr Server, versioned in git as `.pathfinder/workspace.dsl`
- **Code mappings** — `code_path` properties on C4 elements (glob patterns linking source files to components)
- **Documentation** — Markdown sections and ADRs rendered alongside diagrams in Structurizr Server
- **Visualization** — interactive diagrams at `http://localhost:8080`

All model operations go through the Structurizr MCP Server — agents never edit DSL files directly.

## CLI reference

The CLI is thin infrastructure. All model operations go through MCP.

| Command | Description |
|---------|-------------|
| `pathfinder init --name NAME` | Create `.pathfinder/` with config, practices, template DSL |
| `pathfinder install` | Copy skills + agents to `.claude/`, configure MCP server |
| `pathfinder start [--port PORT]` | Start Structurizr Server + MCP Docker containers |
| `pathfinder stop` | Stop both containers |
| `pathfinder info` | Project summary (workspace status, container status) |

All commands accept `--root DIR` (defaults to cwd).

## Best practices config

`.pathfinder/practices.md` contains architectural principles that the Architect Agent follows. Edit it to add project-specific rules:

```markdown
# Architectural Practices

## Principles
- KISS — prefer the simplest solution
- Single Responsibility — each component has one clear purpose

## Conventions
- All new services must use gRPC
- No direct database access from the frontend container
```

## Prerequisites

- **Docker** — for Structurizr Server and MCP server containers
- **Python >= 3.12**
- **Node.js** — for `npx mcp-remote` bridge to MCP server

## Development

```bash
pip install -e ".[dev]"
pytest tests/
pytest tests/ -v --tb=short
```
