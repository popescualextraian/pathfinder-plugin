# Pathfinder Usage Guide

Pathfinder is an AI coding plugin — skills and an architect agent that give Claude Code or Copilot architectural awareness of your project. This guide covers how to set up Pathfinder in a project and how the skills-driven workflow operates.

For a quick overview, see the [README](../README.md).

## Table of Contents

- [Setting Up](#setting-up)
- [The Skills Workflow](#the-skills-workflow)
- [Architecture Model](#architecture-model)
- [CLI Reference](#cli-reference)

---

## Setting Up

### Install Pathfinder

```bash
pip install git+https://github.com/popescualextraian/pathfinder-plugin.git
```

### Install into a project

Run from your project's root:

```bash
# Copy skills and architect agent into the project
pathfinder install

# Initialize the architecture graph
pathfinder init --name "ecommerce-platform"
```

This creates:
- `skills/` — five skill files that Claude Code discovers automatically
- `agents/system-architect.md` — the architect agent
- `.pathfinder/` — the architecture graph (YAML components + generated index)

Custom directories:

```bash
pathfinder install --skills-dir .claude/skills --agents-dir .claude/agents
```

### Add to CLAUDE.md

`pathfinder install` prints a snippet to add to your project's `CLAUDE.md`. This tells Claude Code about the available skills and how to use them.

---

## The Skills Workflow

The skills are the primary interface. They call CLI commands under the hood — you don't run the CLI directly during normal use.

### 1. Discover — onboard an existing codebase

Use the **pathfinder-discover** skill when joining a project or onboarding a repository into Pathfinder. It:

- Analyzes project structure, frameworks, and entry points
- Identifies components (services, libraries, infrastructure)
- Maps code files to components
- Generates the initial `.pathfinder/` graph

This is a one-time operation per project.

### 2. Define — design architectural changes

Use the **pathfinder-define** skill when a new capability or requirement needs architectural work. It:

- Captures the business requirement
- Identifies which components are affected or need to be created
- Defines contracts (inputs/outputs) before any code is written
- Establishes data flows between components
- Works across multiple components at once — the unit of design is a flow, not a single component

### 3. Navigate — load context for a task

Use the **pathfinder-navigate** skill before starting any development task. It:

- Finds the relevant component(s) for a file path or task description
- Loads the architectural slice: component spec, contracts, dependencies, flows
- Limits context to 2 levels deep — enough to understand boundaries without flooding tokens
- Shows what a change will affect before you make it

### 4. Implement — TDD within component boundaries

Use the **pathfinder-implement** skill for each implementation task. It:

- Loads the target component's spec and contracts
- Writes tests first based on the contract
- Implements until tests pass
- Maps new code files back to the component

Each task targets exactly one component. The architect agent sequences tasks so leaf dependencies are implemented first.

### 5. Check — verify after changes

Use the **pathfinder-check** skill in two modes:

**Impact mode** (before changes):
- Analyzes which components a proposed change would affect
- Shows contract dependencies and flow paths
- Identifies risk level

**Health mode** (after changes):
- Runs structural validation (missing parents, broken references, duplicate IDs)
- Detects drift (code mappings that match no files, unmapped components)
- Verifies the graph is consistent

### The Architect Agent

The system architect agent orchestrates the full workflow for non-trivial requirements:

1. Receives a business requirement (feature, bug, tech debt)
2. Uses **navigate** to understand the current architecture
3. Runs **check** in impact mode to determine blast radius
4. Decomposes the requirement into component-scoped changes
5. Uses **define** to formalize new/changed contracts and flows
6. Produces sequenced implementation tasks (leaf-first)
7. Presents the plan for review

The architect does not write code. Implementation is delegated to the **implement** skill, one component at a time.

---

## Architecture Model

### Components

A component is a node in a hierarchical DAG. It represents any architectural unit — a system, service, module, library, database, infrastructure, etc.

```bash
# Add top-level components
pathfinder add system "E-Commerce Platform"
pathfinder add service "Order Service"
pathfinder add database "Order DB"

# Nested hierarchy
pathfinder add module "Payments" --parent e-commerce-platform
pathfinder add service "Gateway" --parent payments

# External systems you depend on but don't own
pathfinder add service "Stripe API" --external
```

Components have:
- **id** — auto-generated dot notation (`payments.gateway`)
- **type** — advisory hint (`system`, `service`, `module`, etc.)
- **status** — lifecycle: `proposed`, `active`, `deprecated`
- **spec** — free-form description for AI agents to interpret
- **contracts** — free-form inputs/outputs
- **tags** — cross-cutting labels (`pci-scope`, `team-payments`)

### Data Flows

What data moves between components, how, and why.

```bash
pathfinder flow-add orders payments --data "PaymentRequest" --protocol REST
pathfinder flow-add payments ledger --data "Transaction" --protocol kafka --pattern publish
```

Trace how data gets from A to B through the graph:

```bash
pathfinder trace orders reports
# orders -> payments -> ledger -> reports
```

### Contracts

What a component accepts and produces. Free-form — designed for AI agents to interpret, not rigid schema validation.

```bash
pathfinder contract-add payments --input \
  --name ProcessPayment \
  --format "POST /api/payments {amount, currency, card_token}" \
  --source orders

pathfinder contract-add payments --output \
  --name PaymentResult \
  --format "{status: 'success'|'failed', transaction_id: string}" \
  --target orders
```

### Structural Dependencies

Dependencies that aren't data flows — build-time, library, infrastructure.

```bash
pathfinder depend orders auth
```

### Code Mappings

Link source files to components. Supports multiple repos.

```bash
pathfinder map payments --glob "src/services/payment/**/*.py"
pathfinder map payments --glob "terraform/modules/payment/**" --repo infra

# Which component owns this file?
pathfinder mapped src/services/payment/gateway.py

# Components with no mappings
pathfinder unmapped
```

### Specs

Free-form text describing what a component does. AI agents interpret these as implementation guidance.

```bash
pathfinder set payments.gateway --spec "Handles payment initiation, validates card details, routes to processor"
pathfinder set payments.gateway --spec-file specs/gateway.md
```

---

## CLI Reference

The CLI maintains the architecture graph that skills operate on. During normal workflow you interact through skills, not these commands directly.

### Project commands

| Command | Description |
|---------|-------------|
| `install [--skills-dir DIR] [--agents-dir DIR]` | Install skills and agent into a project |
| `init --name NAME` | Initialize `.pathfinder/` |
| `info` | Project summary |
| `standards` | Show architectural standards |

### Component commands

| Command | Description |
|---------|-------------|
| `add TYPE NAME [--parent ID] [--external]` | Add a component |
| `set ID [options]` | Update status, type, tags, spec |
| `remove ID [--force] [--dry-run]` | Remove component and children |
| `move ID --parent NEW_PARENT` | Move under a new parent |
| `list [--level N]` | Component tree |
| `show ID [--contracts]` | Component details |
| `children ID` | Direct children |
| `search [QUERY] [--tag T] [--type T] [--status S]` | Search |

### Dependency and flow commands

| Command | Description |
|---------|-------------|
| `deps ID` | What a component depends on |
| `dependents ID` | What depends on a component |
| `depend ID TARGET [--remove]` | Add/remove structural dependency |
| `flows [ID]` | Show data flows |
| `flow-add FROM TO --data DESC [--protocol P] [--pattern P]` | Add a data flow |
| `trace FROM TO` | Trace path between components |

### Code mapping commands

| Command | Description |
|---------|-------------|
| `map ID --glob PATTERN [--repo REPO]` | Map files to a component |
| `mapped FILE` | Find owner of a file |
| `unmapped` | Components with no mappings |

### Contract commands

| Command | Description |
|---------|-------------|
| `contract-add ID --input/--output --name N --format F [--source/--target S] [--version V]` | Add a contract |
| `contract-remove ID --name N` | Remove a contract |

### Validation and export

| Command | Description |
|---------|-------------|
| `validate [--ci]` | Structural integrity check |
| `drift check [--ci]` | Detect architectural drift |
| `export --format {json,dot,markdown}` | Export the graph |

All commands accept `--root DIR` (defaults to cwd or `PATHFINDER_ROOT`). `--ci` exits with code 1 on issues.

### CI integration

```yaml
- name: Validate architecture
  run: |
    pip install -e .
    pathfinder validate --ci
    pathfinder drift check --ci
```

### Project root resolution

Every command resolves the project root:
1. `--root DIR` flag (if provided)
2. `PATHFINDER_ROOT` environment variable
3. Current working directory
