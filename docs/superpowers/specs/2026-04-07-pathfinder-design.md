# Pathfinder — Architecture-First Component Library

## Overview

Pathfinder is a CLI tool + skills layer that models applications as a hierarchy of components with data flows. It replaces feature/spec-driven development with architecture-driven development, where every piece of code is mapped to a component in a living architectural model.

**Core idea:** Instead of Spec (feature) → Plan (tasks) → Code, the workflow becomes Component Map → Component Specs (API, contracts, data flows) → Implementation. Components are the unit of work, not tasks.

**Key differentiator:** Spec-driven dev focuses on "what to build." Pathfinder maintains the relationship between code and its architectural home — "where does it live, what does it connect to, how does data flow through it."

## Users

- **Senior developers / tech leads** — define and maintain the component model
- **All developers** — work within the model, understand where changes belong and what they affect
- **AI agents** — use the model as architectural guardrails for code generation

## Component Model

A component is a node in a hierarchical graph. A component can contain components (fractal nesting — boxes within boxes). At any level, a component looks the same from the outside: it has a spec, contracts, inputs, outputs.

### Component Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique dot-notation slug (e.g., `payment.gateway`) |
| `name` | string | Human-readable name |
| `type` | enum | Abstraction hint: `system`, `module`, `service`, `component`, `sub-component` |
| `status` | enum | Lifecycle: `proposed`, `active`, `deprecated` |
| `parent` | string | Parent component ID |
| `children` | string[] | Child component IDs (derived from hierarchy) |
| `spec` | free-form | Purpose, behavior, constraints — any format the LLM can interpret |
| `contracts` | structured + free-form | Inputs/outputs with flexible format (OpenAPI, TS interface, bullet points) |
| `dataFlows` | structured | Named connections to/from other components with data description and protocol |
| `codeMappings` | structured | Files/repos mapped to this component (supports multiple codebases) |
| `tags` | string[] | Cross-cutting concerns, grouping, namespacing |

### Design Decisions

- **`type` is a hint, not a constraint** — the hierarchy defines nesting, type helps humans orient
- **`spec` and `contracts` are free-form** — the LLM interprets them, no rigid schema on content
- **`codeMappings` support multiple repos** — one component can span codebases (e.g., Terraform + Lambda code + shared layers)
- **`tags` handle cross-cutting concerns** — query across the graph by tag (e.g., "everything tagged `pci-scope`")

### Example Component File

```yaml
# .pathfinder/components/payment/gateway/_component.yaml
id: payment.gateway
name: Payment Gateway
type: service
status: active

spec: |
  Handles all payment processing for the platform.
  - Supports credit card, bank transfer, and wallet payments
  - Retries failed transactions up to 3 times with exponential backoff
  - All transactions are idempotent (uses client-generated transaction ID)

contracts:
  inputs:
    - name: ProcessPayment
      format: |
        POST /api/payments
        { orderId, amount, currency, method, transactionId }
      source: order.checkout
  outputs:
    - name: PaymentResult
      format: |
        { transactionId, status: "success" | "failed" | "pending", providerRef }
      target: order.fulfillment
    - name: PaymentEvent
      format: "CloudEvent { type: payment.completed | payment.failed }"
      target: notification.dispatcher

dataFlows:
  - to: ledger.transactions
    data: "Transaction record for accounting"
    protocol: async/event
  - from: auth.token-manager
    data: "Merchant credentials"
    protocol: sync/internal

codeMappings:
  - repo: backend
    glob: "src/payment/gateway/**"
  - repo: infra
    glob: "terraform/modules/payment-gateway/**"

tags:
  - pci-scope
  - customer-facing
```

## Storage

### Directory Structure

```
.pathfinder/
  config.yaml                    # project config, repo mappings
  standards.yaml                 # project-wide rules and conventions (free-form)
  components/
    system.yaml                  # root component
    payment/
      _component.yaml            # Payment Module spec
      gateway/
        _component.yaml          # Gateway service
      invoice/
        _component.yaml          # Invoice service
    auth/
      _component.yaml
  index.json                     # auto-generated flat graph for fast queries
```

- **YAML files are the source of truth** — human-editable, version controlled, diffable
- **`index.json` is a generated index** — contains the full graph (nodes + edges) flattened for fast traversal
- **Index rebuild strategy** — the index is rebuilt on write commands (add, remove, move, flow-add, map) and lazily on read commands only if stale (missing or older than any `_component.yaml` file). This avoids rebuilding on every read while keeping the index fresh after mutations
- **Folder hierarchy matches component hierarchy** — intuitive navigation
- **`_component.yaml` prefix** avoids collision with child folders
- **ID-to-path enforcement** — the CLI is the authority on the mapping between `id` and folder path. The index builder validates that each component's `id` matches its folder location and reports errors for mismatches. Direct YAML edits that break this mapping are caught at index build time

### Project Configuration

```yaml
# .pathfinder/config.yaml
name: "My Platform"
repos:
  backend:
    path: ../backend-service
  infra:
    path: ../infrastructure
  layers:
    path: ../shared-layers

integrations:
  lsp:
    enabled: auto       # use if available, skip if not
```

### Standards File

A single free-form file for project-wide knowledge — tech stack, testing conventions, deployment rules, code style. Inherited as context by all skills.

```yaml
# .pathfinder/standards.yaml
spec: |
  Tech Stack:
  - TypeScript with NestJS for backend services
  - Python with FastAPI for data pipelines
  - Terraform for all infrastructure

  Testing:
  - vitest for TypeScript, pytest for Python
  - Integration tests against Docker compose

  API Conventions:
  - REST with OpenAPI 3.1
  - All endpoints authenticated except /health
```

## CLI — `pathfinder`

### Define & Manage

```bash
pathfinder init                              # initialize .pathfinder/ in a project
pathfinder add <type> <name> --parent <id>   # add a component
pathfinder set <id> --status <s> --tag <t>   # update fields without opening editor
pathfinder remove <id>                       # remove (recursive with warnings)
pathfinder move <id> --parent <new-parent>   # restructure hierarchy
```

**Remove behavior:** `pathfinder remove <id>` deletes the component and all its children recursively. Before deletion, it warns about:
- Child components that will be removed
- Data flows from other components that reference this component or its children
- Use `--force` to skip the confirmation prompt. Use `--dry-run` to see what would be deleted without doing it.

### Navigate & Query

```bash
pathfinder list                              # tree view of all components
pathfinder list --level 2                    # tree truncated at depth 2
pathfinder info                              # project summary (name, component count, last indexed)
pathfinder show <id>                         # full spec of a component
pathfinder show <id> --contracts             # just the contracts
pathfinder children <id>                     # direct children
pathfinder deps <id>                         # what this component depends on
pathfinder dependents <id>                   # what depends on this component
pathfinder search <query>                    # search by name, tag, or type
pathfinder search --tag pci-scope            # find all components with a tag
pathfinder search --type service             # find all components of a type
```

### Data Flow

```bash
pathfinder flows                             # all data flows
pathfinder flows <id>                        # flows in/out of a component
pathfinder trace <id-a> <id-b>              # shortest path from A to B via data flows
pathfinder flow add <from> <to> --data "X"  # define a flow
```

**Trace algorithm:** `trace` uses BFS to find the shortest path between two components through data flows. It returns a single path, not all possible paths.

### Code Mapping & Drift

```bash
pathfinder map <id> --glob "src/payment/**"  # map code to component
pathfinder unmapped                          # find code not mapped to any component
pathfinder mapped <file-path>                # which component owns this file?
pathfinder drift check                       # compare specs vs actual code
pathfinder drift check --ci                  # exit code 1 if drift found (for CI pipelines)
```

**CI integration:** `pathfinder drift check --ci` returns exit code 1 when drift is detected, making it suitable as a PR gate or CI step. Teams can add it to their CI pipeline to prevent unacknowledged architectural drift from being merged.

### Validation

```bash
pathfinder validate                          # structural integrity check
```

**Validate checks:**
- All parent references point to existing components
- All data flow targets/sources reference existing components
- Component IDs match their folder paths
- No orphaned YAML files without valid component structure
- No duplicate IDs

This is separate from `drift check` (which compares specs vs code). `validate` checks the internal consistency of the component model itself.

### Discovery (Brownfield)

```bash
pathfinder discover                          # AI analyzes codebase, proposes component map
pathfinder discover --repo backend           # discover from a specific repo
pathfinder discover --dry-run                # preview proposals without writing files
```

**Discovery is skill-driven.** The `discover` CLI command is a thin wrapper — the actual analysis is performed by the `pathfinder-discover` skill, which uses the LLM to analyze the codebase. The command:
1. Scans directory structure, entry points, config files, imports
2. Outputs a **proposed component map** as a preview (YAML to stdout)
3. With `--dry-run`, stops after preview. Without it, prompts for confirmation before writing
4. After confirmation, writes component YAML files and builds the index

**Expectations:** Discovery is a starting point, not a finished product. It works best on well-structured codebases with clear directory boundaries. Messy codebases will require more manual curation. The skill guides the user through reviewing and refining the proposals.

### Standards

```bash
pathfinder standards                         # show project standards
```

### Export

```bash
pathfinder export --format json              # full graph as JSON (for AI consumption)
pathfinder export --format dot               # Graphviz diagram
pathfinder export --format markdown          # human-readable doc
```

**Output principle:** Every command outputs concise, structured text. When Claude calls these, it gets exactly what it needs — minimal tokens, maximum information.

### Standalone Value

The CLI works fully without Claude Code or any AI agent. Developers can use it as a lightweight architecture-as-code tool: define components, track data flows, detect drift, export diagrams. The skills and agents enhance the experience with AI-driven workflows, but the core CLI has standalone value for any team that wants to maintain a living architectural model.

## Skills Layer

Skills are Claude Code skills that orchestrate `pathfinder` during development. They work at the **architecture/flow level** — designing multiple components and their relationships together, not one component at a time.

### `pathfinder-discover`

- **Trigger:** Brownfield projects, onboarding a new repo
- **Flow:** Analyze codebase → propose full component map → user validates/refines
- **Output:** Initialized `.pathfinder/` with component hierarchy and data flows

### `pathfinder-define`

- **Trigger:** Greenfield projects, adding new capability
- **Flow:** Start from business description → guide toward architectural decomposition → define components, contracts, and data flows together as a coherent system
- **Output:** New/updated component YAML files + flows

### `pathfinder-navigate`

- **Trigger:** Any development task that needs orientation
- **Flow:** "I need to change X" → `pathfinder mapped <file>` → find owning component → load relevant spec + connected components
- **Purpose:** Token-efficient context loading — only loads the relevant slice of the graph

### `pathfinder-implement`

- **Trigger:** Component specs are ready, time to generate code
- **Flow:** Load component spec + contracts + standards → generate implementation → map code back to component
- **Constraint:** Respects contracts between components — checks inputs/outputs match

### `pathfinder-check`

- **Trigger:** Before major changes, periodic health check
- **Flow:** Drift detection (specs vs code) + impact analysis (what would this change affect?)
- **Output:** Report of mismatches, guidance to update spec or fix code

## Integrations

**Provider pattern:** Pathfinder has a code analysis interface. The default provider uses glob patterns + LLM code reading. Optional providers enhance capabilities:

- **LSP:** Better code mapping (resolve imports, find references, type hierarchies), smarter drift detection, richer discovery from actual call graphs
- **Serena / AST tools:** Deeper structural understanding for discovery and change detection

Integrations are **auto-detected when available, gracefully absent when not**. Zero dependencies to start.

## Architecture Modes

- **Greenfield:** Human + AI define architecture upfront → components become scaffolding for implementation
- **Brownfield:** AI analyzes codebase → proposes component hierarchy → human validates → model becomes the living architecture
- **Ongoing:** Monitor for drift between specs and code → reconcile → architecture stays alive

## Agents

### System Architect Agent (v1)

The primary agent — bridges business requirements to architectural decisions. This is the agent users interact with when planning work.

**Responsibilities:**
- Takes business requirements / feature descriptions as input
- Uses `pathfinder-navigate` to understand current architecture
- Uses `pathfinder-define` to decompose requirements into component updates
- Produces implementation tasks scoped to components (not features)
- Ensures every task maps to a component with clear contracts

**Workflow:**
```
Business requirement
  → Architect Agent identifies affected components
  → Updates/creates component specs via pathfinder-define
  → Produces implementation plan (tasks per component)
  → Hands off to implementation (default Claude agent + skills)
```

**Implementation approach:** The architect agent is a Claude Code agent definition (markdown prompt in `agents/`). It orchestrates pathfinder skills and the CLI. It does not implement code — it plans and delegates.

### Implementation Approach

For v1, implementation tasks are executed by the **default Claude agent** using pathfinder skills (`pathfinder-implement`, `pathfinder-navigate`, `pathfinder-check`). The skills provide architectural guardrails. If guardrails prove insufficient, a dedicated implementation agent can be introduced later.

**TDD is built into the implementation flow.** The `pathfinder-implement` skill follows a red-green-refactor cycle:
1. Write failing test based on component contract
2. Implement until test passes
3. Refactor, verify drift check passes

### Future Agents (out of scope for v1)

- **Review Agent** — validates implementation against component specs and contracts
- **Testing Agent** — generates and maintains test suites per component
- **Drift Agent** — periodic architectural health checks

These are mentioned for completeness. They will be designed when the core system is stable.

## Tech Stack

- **Language:** Python 3.12+
- **CLI framework:** click
- **Storage:** YAML files (source of truth) + JSON index (generated)
- **YAML parsing:** PyYAML
- **Glob matching:** pathlib + fnmatch (stdlib)
- **Testing:** pytest
- **Graph operations:** In-memory adjacency list, rebuilt from index
- **Output:** Structured text for CLI, JSON flag for machine consumption

## Project Structure

```
pathfinder/
  pathfinder/                     # Python package
    __init__.py
    types.py                      # shared types (dataclasses)
    cli/
      __init__.py
      main.py                     # click group, registers all commands
      init.py
      add.py
      set.py
      remove.py
      move.py
      list.py
      info.py
      show.py
      search.py
      deps.py
      flows.py
      map.py
      drift.py
      validate.py
      discover.py
      standards.py
      export.py
      utils.py
    core/
      __init__.py
      storage.py                  # read/write YAML files
      index_builder.py            # index builder (YAML -> JSON)
      graph.py                    # graph operations (traverse, trace, deps)
    integrations/
      __init__.py
      lsp.py                      # optional LSP provider
      code_analyzer.py            # glob-based default provider
  skills/
    pathfinder-discover/
      SKILL.md
    pathfinder-define/
      SKILL.md
    pathfinder-navigate/
      SKILL.md
    pathfinder-implement/
      SKILL.md
    pathfinder-check/
      SKILL.md
  agents/
    system-architect.md            # architect agent prompt
  tests/
    core/
      test_storage.py
      test_index_builder.py
      test_graph.py
    cli/
      test_init.py
      test_add.py
      ...
  pyproject.toml
```

## Key Principles

- **Architecture-first, not feature-first** — components are the unit of work
- **Boxes and lines** — simple model, infinite depth, no framework ceremony
- **Design at flow level** — design multiple components together, implement per component
- **Flexible content** — specs and contracts in any format the LLM can interpret
- **Living architecture** — drift detection keeps the model in sync with reality
- **Multi-repo native** — one component can span codebases
- **Token-efficient** — CLI returns exactly what's needed, no file scanning
- **Zero mandatory dependencies** — works standalone, integrations enhance
