# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## What Pathfinder Is

Pathfinder is an **AI coding plugin** — skills and an architect agent that give AI coding tools (Claude Code, Copilot) a structured understanding of a project's architecture. Components, data flows, contracts, and code mappings form a living architecture model that AI agents consume as context and guardrails.

The **CLI** (`pathfinder`) is infrastructure that maintains the architecture graph. It is not the product — the skills and agent are. Similar to how OpenAPI tooling maintains specs consumed by other tools, the CLI maintains data that skills operate on.

### Distribution

Pathfinder is installed **into** target projects via `pathfinder install`, which copies:
- 5 skills into `skills/` (Claude Code discovers these automatically)
- 1 architect agent into `agents/`
- A CLAUDE.md snippet for the target project

The `.pathfinder/` directory (created by `pathfinder init`) stores the architecture graph as YAML source of truth + a generated JSON index.

## Build & Test

```bash
pip install -e ".[dev]"        # Install in dev mode with pytest
pytest tests/                  # Run all tests
pytest tests/cli/test_add.py   # Run a single test file
pytest tests/ -v --tb=short    # Verbose with short tracebacks
```

Entry point: `pathfinder = "pathfinder.cli.main:cli"` (Click CLI, Python >=3.12).
Dependencies: click>=8.1, pyyaml>=6.0. Dev: pytest>=8.0. Build: hatchling.

## Product Surface: Skills & Agent

### Skills (5)

Installed into target projects. Each skill is a procedure that an AI coding tool follows, calling the CLI under the hood.

| Skill | Purpose |
|-------|---------|
| **pathfinder-discover** | Onboard an existing codebase — analyze and generate the component map |
| **pathfinder-define** | Decompose business requirements into components, contracts, and flows |
| **pathfinder-navigate** | Load the relevant architectural slice before a task (token-efficient) |
| **pathfinder-implement** | TDD implementation scoped to component boundaries |
| **pathfinder-check** | Health checks, drift detection, impact analysis |

Skills live in `pathfinder/skills/`. Each is a `SKILL.md` with structured procedures.

### System Architect Agent

`pathfinder/agents/system-architect.md` — the primary agent. Takes business requirements, navigates the architecture, runs impact analysis, and produces component-scoped implementation tasks. Designs and decomposes; does not write code.

### Workflow

```
Business requirement
  → Architect agent (navigate → impact → decompose → define contracts → sequence tasks)
    → Implementation tasks (one per component, leaf-first)
      → pathfinder-implement skill (TDD per component)
        → pathfinder-check (verify after)
```

## CLI Architecture (Infrastructure)

The CLI exists to serve the skills. Three layers:

1. **`pathfinder/core/`** — Business logic, no CLI awareness
   - `storage.py` — YAML file I/O. Component IDs use dot notation (`payment.gateway`) → paths (`payment/gateway/_component.yaml`).
   - `index_builder.py` — Builds `index.json` (flat graph) from YAML. Lazy rebuild: stale-checked on reads, always rebuilt on writes.
   - `graph.py` — Graph queries: deps, dependents, flows, BFS trace, tag queries, code path matching (glob specificity ranking).

2. **`pathfinder/cli/`** — Click commands, one file per command
   - Each command resolves project root via `utils.resolve_root()` (`--root` flag > `PATHFINDER_ROOT` env > cwd).
   - Mutations call core functions then `build_index()`. Reads call `ensure_index()`.
   - `install_cmd.py` — copies skills + agent into target projects.

3. **`pathfinder/types.py`** — Shared dataclasses (`Component`, `DataFlow`, `CodeMapping`, `Contracts`, etc.). No external imports.

## Data Model

The architecture graph that skills consume:

- **Component** — id (dot-notation), type (advisory), status, parent, spec (free-form), contracts (free-form), data_flows, code_mappings, tags, dependsOn, external flag.
- **Index** (`index.json`) — Generated flat graph: `components` dict + `flows` list. Derived from YAML source of truth.
- **Storage** (`.pathfinder/`) — `config.yaml`, `standards.yaml`, `components/` (hierarchical YAML), `index.json` (generated).

Key decisions:
- `spec` and `contracts` are free-form text for LLM interpretation, not rigid schemas.
- `code_mappings` support multiple repos (one component can span Terraform + Lambda).
- `tags` handle cross-cutting concerns (e.g., query all `pci-scope` components).
- Hierarchy is structural; `type` is advisory.

## CLI Command Pattern

```python
@click.command("name")
@click.argument("arg")
@click.option("--root", default=None)
def name_cmd(arg, root):
    project_root = resolve_root(root)
    # call core functions
    # rebuild index if mutating
    click.echo(result)
```

## Test Pattern

CLI tests use Click's `CliRunner` with a `tmp_path` fixture for isolated `.pathfinder/` directories. Core tests build minimal component graphs in-memory.
