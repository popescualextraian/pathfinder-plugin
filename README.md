# Pathfinder

Architecture-driven development plugin for AI coding tools. Install into any project to give Claude Code or Copilot a structured understanding of your system — components, data flows, contracts, and code mappings.

## How it works

Pathfinder adds **five skills** and an **architect agent** to your project. The skills teach your AI coding tool to think architecturally — decomposing work by component boundaries instead of feature specs. A CLI maintains the architecture graph underneath, but you interact through skills, not commands.

```
Business requirement
  → Architect agent (navigate → impact analysis → decompose → define contracts)
    → Implementation tasks (one per component, leaf-first)
      → pathfinder-implement skill (TDD within component boundaries)
        → pathfinder-check (verify after changes)
```

### Skills

| Skill | What it does |
|-------|-------------|
| **pathfinder-discover** | Analyze an existing codebase and generate the component map |
| **pathfinder-define** | Decompose requirements into components, contracts, and flows |
| **pathfinder-navigate** | Load only the relevant architectural slice for a task |
| **pathfinder-implement** | TDD implementation scoped to component boundaries |
| **pathfinder-check** | Health checks, drift detection, and impact analysis |

### System Architect Agent

The architect agent bridges business requirements to component-scoped implementation tasks. It navigates the current architecture, runs impact analysis, decomposes work into component changes, defines contracts first, and sequences tasks leaf-first. It designs and delegates — it does not write code.

## Installation

Requires **Python 3.12+**.

```bash
pip install git+https://github.com/popescualextraian/pathfinder-plugin.git
```

## Setting up a project

Pathfinder is installed **into** each project that uses it:

```bash
# 1. Install skills and architect agent into your project
pathfinder install

# 2. Initialize the architecture graph
pathfinder init --name my-project
```

`pathfinder install` copies skills into `skills/` and the architect agent into `agents/`. It also prints a CLAUDE.md snippet to add to your project so Claude Code discovers the skills automatically.

### Custom directories

```bash
pathfinder install --skills-dir .claude/skills --agents-dir .claude/agents
```

### What gets installed

```
your-project/
  skills/
    pathfinder-discover/SKILL.md
    pathfinder-define/SKILL.md
    pathfinder-navigate/SKILL.md
    pathfinder-implement/SKILL.md
    pathfinder-check/SKILL.md
  agents/
    system-architect.md
  .pathfinder/                    # Created by pathfinder init
    config.yaml
    components/
    index.json
```

## Typical workflow

### 1. Onboard an existing codebase

Use the **pathfinder-discover** skill. It analyzes your project structure and generates the initial component map — systems, services, libraries, and their relationships.

### 2. Design changes architecturally

When a new requirement arrives, the **architect agent** takes over:
- Navigates the current architecture to understand the affected area
- Runs impact analysis to determine blast radius
- Decomposes the requirement into component-scoped changes
- Defines contracts before any implementation starts
- Sequences tasks by dependency (leaf components first)

### 3. Implement within boundaries

Each implementation task targets a single component. The **pathfinder-implement** skill:
- Loads the component's spec and contracts
- Writes tests first (TDD)
- Implements until tests pass
- Maps code back to the component

### 4. Verify after changes

The **pathfinder-check** skill detects drift, validates structural integrity, and confirms contracts are satisfied.

## Architecture model

The graph the skills operate on:

- **Components** — nodes in a hierarchical DAG. Each has an id (dot-notation like `payment.gateway`), type (advisory), status, spec (free-form), contracts (free-form), data flows, code mappings, tags, and structural dependencies.
- **Data flows** — what data moves between components, via which protocol, in which pattern (request/response, publish/subscribe).
- **Contracts** — what a component accepts and produces. Free-form text that AI agents interpret, not rigid schemas.
- **Code mappings** — glob patterns linking source files to components. Supports multiple repos.

Everything is stored in `.pathfinder/` as YAML (source of truth) with a generated `index.json` for fast graph queries.

## CLI reference

The CLI maintains the architecture graph. Skills call these commands under the hood — you typically don't need to run them directly.

### Project

| Command | Description |
|---------|-------------|
| `install [--skills-dir DIR] [--agents-dir DIR]` | Install skills and agent into a project |
| `init --name NAME` | Initialize `.pathfinder/` |
| `info` | Project summary (counts by type, tags, flows) |
| `standards` | Show architectural standards |

### Components

| Command | Description |
|---------|-------------|
| `add TYPE NAME [--parent ID] [--external]` | Add a component |
| `set ID [--status S] [--type T] [--tag T] [--remove-tag T] [--spec TEXT] [--spec-file FILE]` | Update fields |
| `remove ID [--force] [--dry-run]` | Remove a component and its children |
| `move ID --parent NEW_PARENT` | Move under a new parent |

### Viewing and search

| Command | Description |
|---------|-------------|
| `list [--level N]` | Component tree |
| `show ID [--contracts]` | Component details |
| `children ID` | Direct children |
| `search [QUERY] [--tag T] [--type T] [--status S]` | Search components |

### Dependencies and data flows

| Command | Description |
|---------|-------------|
| `deps ID` | What a component depends on |
| `dependents ID` | What depends on a component |
| `depend ID TARGET [--remove]` | Add/remove structural dependency |
| `flows [ID]` | Data flows (all or per component) |
| `flow-add FROM TO --data DESC [--protocol P] [--pattern P]` | Add a data flow |
| `trace FROM TO` | Trace path between components |

### Code mappings

| Command | Description |
|---------|-------------|
| `map ID --glob PATTERN [--repo REPO]` | Map files to a component |
| `mapped FILE` | Find which component owns a file |
| `unmapped` | Components with no code mappings |

### Contracts

| Command | Description |
|---------|-------------|
| `contract-add ID --input/--output --name N --format F [--source S] [--target T] [--version V]` | Add a contract |
| `contract-remove ID --name N` | Remove a contract |

### Validation and export

| Command | Description |
|---------|-------------|
| `validate [--ci]` | Structural integrity check |
| `drift check [--ci]` | Detect architectural drift |
| `export --format {json,dot,markdown}` | Export the graph |

All commands accept `--root DIR` (defaults to cwd or `PATHFINDER_ROOT` env var). The `--ci` flag exits with code 1 when issues are found.

## Storage

```
.pathfinder/
  config.yaml            # Project name, allowed component types
  standards.yaml         # Architectural standards (optional)
  components/            # One YAML file per component
    payment/
      _component.yaml
      gateway/
        _component.yaml
  index.json             # Generated graph index (auto-rebuilt)
```

Component IDs use dot notation mapped to directory paths: `payment.gateway` → `components/payment/gateway/_component.yaml`. The `index.json` is always derived from YAML — safe to delete and regenerate.

## CI integration

```yaml
- name: Validate architecture
  run: |
    pip install -e .
    pathfinder validate --ci
    pathfinder drift check --ci
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/
pytest tests/ -v --tb=short
```
