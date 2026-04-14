# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## What Pathfinder Is

Pathfinder is an **AI coding plugin** — agents and skills that give AI coding tools (Claude Code, Copilot) a structured understanding of a project's architecture using the **Structurizr ecosystem** and **C4 model standard**.

The architecture model lives in Structurizr DSL, managed via the **Structurizr MCP Server** (AI interface) and visualized via the **Structurizr Server** (Docker). The **CLI** (`pathfinder`) is thin infrastructure — init, install, Docker lifecycle. All model operations go through MCP.

### Distribution

Pathfinder is installed **into** target projects via `pathfinder install`, which copies:
- 2 skills into `.claude/skills/` (Claude Code discovers these automatically)
- 2 agents into `.claude/agents/`
- MCP server configuration into Claude Code settings

The `.pathfinder/` directory (created by `pathfinder init`) stores `workspace.dsl` (Structurizr source of truth), `config.yaml`, and `practices.md`.

## Build & Test

```bash
pip install -e ".[dev]"        # Install in dev mode with pytest
pytest tests/                  # Run all tests
pytest tests/cli/test_init.py  # Run a single test file
pytest tests/ -v --tb=short    # Verbose with short tracebacks
```

Entry point: `pathfinder = "pathfinder.cli.main:cli"` (Click CLI, Python >=3.12).
Dependencies: click>=8.1, pyyaml>=6.0. Dev: pytest>=8.0. Build: hatchling.

## Product Surface: Agents & Skills

### Agents (2)

| Agent | Purpose |
|-------|---------|
| **Init Agent** | Scans codebase, builds complete C4 model + documentation via MCP, maps all code |
| **System Architect** | Takes business requirements, produces implementation specs. Designs, does not code. |

Agents live in `pathfinder/agents/`. Each is a markdown file with structured procedures.

### Skills (2)

| Skill | Purpose |
|-------|---------|
| **pathfinder-context** | Subagent: extracts relevant architectural slice from workspace for a given query |
| **pathfinder-review** | Interactive review loop: walk through C4 levels with user, collect corrections |

Skills live in `pathfinder/skills/`. Each is a `SKILL.md` with structured procedures.

### Workflow

```
Flow 1: Init
  User runs Claude /init, then starts Init Agent in fresh context
    → Scans codebase → Builds C4 model via MCP → Maps all code → Visual review

Flow 2: Design
  User provides business requirement
    → Architect Agent → Context skill (subagent) extracts relevant slice
    → Explore alternatives → Before/after visualization → Update model via MCP
    → Produce implementation spec
```

## CLI Architecture (Infrastructure)

The CLI is thin — only infrastructure. No model commands.

```
pathfinder/
  cli/
    main.py             # Click entry point
    init_cmd.py         # Create .pathfinder/ with config, practices, template DSL
    install_cmd.py      # Copy skills + agents + MCP config to .claude/
    docker_cmd.py       # start/stop for Structurizr Server + MCP containers
    info_cmd.py         # Project summary
  skills/               # 2 skill SKILL.md files
  agents/               # 2 agent .md files
```

### Commands

| Command | Purpose |
|---------|---------|
| `pathfinder init --name NAME` | Create `.pathfinder/` with config, practices, template DSL |
| `pathfinder install` | Copy skills + agents to `.claude/`, configure MCP |
| `pathfinder start` | Start Structurizr Server + MCP Docker containers |
| `pathfinder stop` | Stop both containers |
| `pathfinder info` | Show project summary |

## Key Design Principle

All architecture model operations go through the **Structurizr API via MCP**. The LLM never directly reads or writes workspace files. The Structurizr Server is the system of record.

## Test Pattern

CLI tests use Click's `CliRunner` with a `tmp_path` fixture for isolated `.pathfinder/` directories. Docker commands are tested with mocked `subprocess.run`.
