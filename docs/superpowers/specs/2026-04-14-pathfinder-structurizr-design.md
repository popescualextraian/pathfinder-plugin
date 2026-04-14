# Pathfinder v2: Structurizr/C4 Variant

**Date**: 2026-04-14
**Status**: Design
**Replaces**: v1 (custom YAML/JSON model)

## 1. Overview

Pathfinder v2 replaces the custom architecture model with one built entirely on the **Structurizr ecosystem** and **C4 model standard**. Instead of building a custom model layer, we use Structurizr's own tools:

- **Structurizr DSL** — source of truth for the architecture model
- **Structurizr MCP Server** — AI agents validate, parse, and inspect the model
- **Structurizr Server** — workspace management, API, and visualization via Docker

Custom Python code is minimal — only what Structurizr doesn't provide: a thin CLI for infrastructure and skill orchestration.

### Motivation

1. **Standardization** — C4 is the industry standard. Structurizr is the reference implementation by the C4 author.
2. **No custom model code** — All model operations go through MCP/API. No Python dataclasses, no serializers.
3. **Visual validation** — Structurizr Server gives interactive diagrams out of the box. Users see what the LLM understands.
4. **Full documentation** — Structurizr supports Markdown documentation sections and ADRs attached to elements, not just diagrams.
5. **AI-native** — Structurizr DSL is text-based, diff-friendly, and designed for LLM generation. The MCP server is purpose-built for AI agent integration.
6. **Complete code coverage** — Every source file maps to a C4 component via DSL properties.

### What's Custom vs. What's Structurizr

| Concern | Handled by |
|---------|-----------|
| Architecture model (systems, containers, components, relationships) | **Structurizr DSL** |
| Model validation and inspection | **Structurizr MCP** |
| DSL parsing to JSON | **Structurizr MCP** |
| Documentation sections and ADRs | **Structurizr DSL + Server UI** |
| Visualization | **Structurizr Server** (web UI at :8080) |
| Export to Mermaid/PlantUML | **Structurizr MCP** |
| Project init, Docker lifecycle, skill orchestration | **Custom Python + CLI** |

---

## 2. Architecture

```
+---------------------------------------------------+
|  2 Agents + 2 Skills                               |  Workflow layer
|  Init Agent, Architect Agent                       |  (installed into target projects)
|  Context, Review skills                            |
|  All model operations go through MCP/API           |
+---------------------------------------------------+
|  Structurizr Ecosystem                              |  Model + API layer
|  Server (workspace management, visualization)      |  (official tools, Docker)
|  MCP Server (AI interface: CRUD, validate, export) |
|  DSL (workspace format, git-versioned)             |
+---------------------------------------------------+
|  Pathfinder Python (thin)                           |  Infrastructure layer
|  CLI for init, install, Docker lifecycle           |  (minimal custom code)
+---------------------------------------------------+
```

### Two Core Flows

```
Flow 1: Init
  User starts Init Agent (recommended: run Claude /init first for codebase context, then fresh session)
    → Init Agent scans entire codebase
    → Builds full C4 model + documentation via MCP
    → Maps every source file to a component
    → Opens Structurizr Server for visual review
    → User validates and iterates
    → Commits workspace to git

Flow 2: Design (Architect Agent)
  User provides business requirement (+ specs, mocks, etc.)
    → Architect Agent receives the input
    → Context skill (subagent, fresh context) extracts relevant architectural slice
    → Agent loads best practices from config
    → Agent proposes approach, explores alternatives
    → User validates with before/after visualization
    → Agent updates model via MCP
    → Agent produces implementation spec
```

### Key Design Principle: API-Driven Management

All architecture model operations go through the **Structurizr API via MCP**. The LLM never directly reads or writes workspace files. Instead:

1. **Read** — MCP "Read workspace" retrieves the current model from the server
2. **Create/Update** — MCP "Create/Update workspace" sends DSL to the server
3. **Validate** — MCP "Validate DSL" and "Inspect DSL" check correctness
4. **Query** — MCP "Parse DSL" returns JSON for structured access
5. **Export** — MCP exports views to Mermaid/PlantUML

The **Structurizr Server** is the system of record. It manages persistence, handles visualization, and exposes the workspace API that MCP connects to. DSL files in `.pathfinder/` are the server's storage — committed to git for version control, but managed by the server, not by the LLM.

No custom Python model classes, graph traversal, or DSL parsers. The MCP handles model operations; the LLM reasons over the JSON it returns.

---

## 3. Structurizr DSL — Source of Truth

### File Structure

```
.pathfinder/
  workspace.dsl         # Source of truth — managed by Structurizr Server
  workspace.json        # Layout info — managed by Structurizr Server
  config.yaml           # Pathfinder config (project name, settings)
  practices.md          # Architectural best practices (user-managed)
```

The `.dsl` file is the primary artifact — git-versioned and diff-friendly. Both files are managed by the Structurizr Server (not edited directly). `workspace.json` stores layout information when diagram positions are saved in the UI.

### DSL Conventions

Pathfinder-specific conventions on top of standard Structurizr DSL:

- **`!identifiers hierarchical`** — always enabled. Allows referencing nested elements as `system.container.component`, which skills and agents rely on for navigation.
- **Code mapping properties** on any C4 element:

| Property | Purpose |
|----------|---------|
| `code_path` | Primary glob pattern (e.g. `src/auth/**/*.py`) |
| `code_path_2`, `code_path_3`, ... | Additional patterns (Terraform, configs, etc.) |
| `code_hint` | Human-readable note for mixed or ambiguous files |
| `code_repo` | Repository name for multi-repo setups |

These travel with the model as element properties — no separate mapping file.

Example showing only the Pathfinder-specific parts:

```
workspace "My Project" "Architecture model" {
    !identifiers hierarchical

    model {
        mySystem = softwareSystem "My System" {
            api = container "API" "REST API" "Python/FastAPI" {
                authModule = component "Auth Module" "Handles auth" "Python" {
                    properties {
                        code_path "src/auth/**/*.py"
                    }
                }
                userService = component "User Service" "User accounts" "Python" {
                    properties {
                        code_path "src/users/**/*.py"
                        code_path_2 "terraform/modules/user-db/**/*.tf"
                        code_hint "User RDS instance in shared Terraform"
                    }
                }
            }
        }
    }
    # views, styles, relationships — standard Structurizr DSL
}
```

### Documentation in the Workspace

Structurizr supports Markdown documentation sections and ADRs attached to the workspace or specific software systems. These are rendered alongside diagrams in the Server UI.

```
workspace "My Project" {
    model { ... }
    views { ... }

    !docs docs/arch            # Markdown files from this directory
    !adrs docs/arch/decisions  # ADR files from this directory
}
```

The Init Agent and Architect Agent write documentation into the workspace — not just model elements. This means the Structurizr UI at `:8080` becomes the single place to understand the architecture: diagrams, documentation, and decisions together.

All other DSL syntax (relationships, views, styles, persons, external systems) follows standard Structurizr conventions per https://docs.structurizr.com/dsl.

---

## 4. Structurizr MCP Server

### Role

The MCP server is the AI agent's interface to Structurizr. All model operations go through it:
- **CRUD** — create, read, update, and delete workspaces on the Structurizr Server
- **Validate DSL** — check syntax correctness before applying changes
- **Inspect DSL** — detect architectural issues (missing descriptions, violations)
- **Parse DSL** — convert to JSON for structured queries
- **Export** — generate Mermaid/PlantUML from views

### Setup

The MCP server connects to a Structurizr Server instance. Both run as Docker containers:

```bash
# 1. Start Structurizr Server (manages workspace, provides visualization)
docker run -d \
  --name pathfinder-server \
  -p 8080:8080 \
  -v "$(pwd)/.pathfinder":/usr/local/structurizr \
  structurizr/structurizr server

# 2. Start MCP Server (AI agent interface, connects to Structurizr Server)
docker run -d \
  --name pathfinder-mcp \
  -p 3000:3000 \
  structurizr/mcp -dsl -mermaid -plantuml \
  -server-create -server-read -server-update -server-delete
```

### MCP Tools Available

| Tool | Purpose | When Used |
|------|---------|-----------|
| **Create workspace** | Create a new workspace on the server | Init Agent (initial setup) |
| **Read workspace** | Retrieve current workspace from server | Context skill (read current state) |
| **Update workspace** | Send updated DSL to server (preserves layout) | Architect Agent (apply changes) |
| **Delete workspace** | Remove a workspace | Cleanup |
| **Validate DSL** | Check DSL is parseable, return OK or errors | Before every update |
| **Parse DSL** | Convert DSL to JSON workspace | Context skill (structured queries) |
| **Inspect DSL** | Find violations (missing descriptions, etc.) | Init Agent, Architect Agent |
| **Export to Mermaid** | Generate Mermaid diagram from a view | Before/after visualization |
| **Export to PlantUML** | Generate PlantUML from a view | Alternative export |

### Public Instance

A public MCP instance runs at `https://mcp.structurizr.com/mcp` with DSL and export tools (no server CRUD). Useful for validation during development.

### Claude Code Configuration

```json
{
  "mcpServers": {
    "structurizr": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:3000/mcp"]
    }
  }
}
```

---

## 5. Visualization

The Structurizr Server (started in Section 4) provides the visualization UI at `http://localhost:8080`. No separate visualization tool needed.

### Features

- System Context, Container, and Component diagrams (from views in DSL)
- Documentation sections and ADRs rendered alongside diagrams
- Interactive navigation between C4 zoom levels
- Manual layout editing (saved to `workspace.json`)
- Live updates when workspace is modified via MCP
- Relationship labels showing protocols and descriptions

Managed by `pathfinder start` / `pathfinder stop` (see CLI, Section 9).

---

## 6. Best Practices Config

**File**: `.pathfinder/practices.md`

A user-managed Markdown file containing architectural principles that the Architect Agent reads before proposing changes. Ships with sensible defaults; users customize to their project.

### Default Content

```markdown
# Architectural Practices

## Principles
- KISS — prefer the simplest solution that meets the requirement
- Single Responsibility — each component has one clear purpose
- Loose Coupling — minimize dependencies between components
- High Cohesion — related functionality belongs together

## Conventions
- New components must have code_path mappings
- External integrations are modeled as external software systems
- Database-per-service when services need independent data ownership
- Async communication between containers when possible
```

The Architect Agent reads this file at the start of every design session. Users can add project-specific rules (e.g., "all new services must use gRPC", "no direct database access from the frontend container").

---

## 7. Agents

### 7.1 Init Agent

**File**: `pathfinder/agents/init-agent.md`
**Recommendation**: Suggest the user runs Claude's `/init` first for codebase context — this is a message to the user, not an automated step.
**Best used**: In a fresh context session, before other work.

**Role**: Scans an existing codebase and builds the complete C4 model with documentation.

#### Workflow

1. **Setup**: Check if `.pathfinder/` exists. If not, run `pathfinder init --name <project>`. Ensure infrastructure is running: `pathfinder start`.
2. **Analyze the codebase**:
   - Read directory tree, README, existing docs, CLAUDE.md, package configs
   - Identify deployment boundaries (services, databases, frontends, infrastructure)
   - Identify external systems the project interacts with
   - Identify logical components within each deployable unit
   - Identify technology stack for each unit
3. **Propose a C4 model** to the user (text description):
   - **Level 1 (System Context)**: The system + external actors and systems
   - **Level 2 (Containers)**: Deployable units within the system
   - **Level 3 (Components)**: Logical modules within containers
   - **Relationships**: How elements communicate (protocol, sync/async)
4. **User validates the proposal**. Iterate until approved.
5. **Build the workspace** via MCP "Create workspace":
   - Complete model with systems, containers, components, relationships
   - `code_path` properties on all components — **every source file must be mapped**
   - Views for each system context, container, and component
   - Default styles
   - Documentation sections: system overview, component descriptions, key decisions
6. **Validate**: MCP "Validate DSL" + "Inspect DSL". Fix any issues.
7. **Coverage check**: Verify no source files are unmapped. The agent uses glob/find to list all source files, compares against `code_path` patterns in the workspace. Iterate until complete.
8. **Review flow** (see Review skill, Section 8.2): Open Structurizr Server, walk through each C4 level with the user, collect corrections, apply via MCP.

#### Output

Workspace created on server with:
- Complete C4 model (all levels)
- Every source file mapped to a component
- Documentation sections describing the architecture
- Views for all levels
- User has visually validated the result

#### Principles

- **Complete coverage is non-negotiable** — no source file left unmapped
- **Documentation, not just diagrams** — write Markdown sections explaining why things are structured this way
- **Propose before building** — always get user approval on the text description before composing DSL
- **Visual validation as final step** — the user must see and approve the rendered diagrams

---

### 7.2 Architect Agent

**File**: `pathfinder/agents/system-architect.md`
**Role**: Takes business requirements and produces implementation specs. Designs and decomposes; does NOT write code.

#### Workflow

1. **Receive input** — business requirement, feature request, tech debt. User may also provide specs, mocks, UI screenshots, API docs, or other reference material.
2. **Load best practices** — read `.pathfinder/practices.md`.
3. **Extract context** — dispatch the **Context skill** (Section 8.1) as a subagent with the requirement as input. Receives back the relevant architectural slice: affected components, relationships, code paths, documentation.
4. **Clarify** — ask the user targeted questions based on what the context reveals. E.g., "The current auth module handles sessions — should the new SSO flow replace that or run alongside it?"
5. **Explore alternatives** — propose 2-3 approaches at the right C4 level:
   - Could this be a new component in an existing container, or a new container?
   - What are the tradeoffs? (coupling, deployment independence, data ownership)
   - Evaluate against best practices from config
   - Recommend one option with reasoning
6. **Before/after visualization** — export current view via MCP "Export to Mermaid", then show proposed state. User sees what changes.
7. **User validates**. Iterate until approved.
8. **Apply to model** — compose updated DSL and apply via MCP "Update workspace". Validate with MCP.
9. **Update documentation and ADRs** — update Structurizr documentation sections to reflect the change. If the decision is significant (new container, technology choice, changed integration pattern), write an ADR in the workspace. Documentation and ADRs are visible alongside diagrams in the Structurizr UI.
10. **Produce implementation spec** — write a spec document following the template below. This is the handoff to implementation.

#### 7.2.1 Implementation Spec Template

The architect agent produces this document for each approved design. Saved to `docs/specs/<date>-<feature>.md`.

```markdown
# <Feature Name>

## Requirement
<What was asked for and why>

## Architecture Decision
<Which approach was chosen and why (brief — the model is the source of truth)>

## Affected Components

| Component | C4 Path | Action | Code Paths |
|-----------|---------|--------|------------|
| Auth Module | mySystem.api.authModule | Modified | src/auth/**/*.py |
| Payment Service | mySystem.api.paymentService | **New** | src/payments/**/*.py |
| Database | mySystem.database | Unchanged (new tables) | migrations/**/*.sql |

## New Relationships
- paymentService -> database "Reads/writes payment data" (SQL)
- paymentService -> stripeGateway "Processes payments" (HTTPS)

## Contracts
<What each component expects from its neighbors — inputs, outputs, protocols>

### paymentService -> database
- Expects: payments table with columns [id, user_id, amount, status, created_at]
- Writes: INSERT on payment creation, UPDATE on status change

### api -> paymentService
- Endpoint: POST /api/payments
- Request: { user_id, amount, currency }
- Response: { payment_id, status }

## Implementation Order
<Dependency-ordered, leaf-first. Each task is single-component.>

1. Database migrations (no dependencies)
2. Payment Service (depends on database)
3. API route wiring (depends on payment service)

## Visual Reference
<Link to Structurizr Server or inline Mermaid export showing the before/after>
```

#### Principles

- **Context before design** — always dispatch the Context skill first. Never design blind.
- **Best practices are configurable** — read and follow `.pathfinder/practices.md`. The user controls the rules.
- **Alternatives before decisions** — never jump to a single option. Explore placement, coupling, and deployment tradeoffs.
- **C4 levels matter** — reason at the right zoom level. System Context for boundaries, Containers for deployment, Components for logic.
- **Relationships first** — understand data flow before deciding where to put things.
- **Visual validation always** — show before/after diagrams. They catch misunderstandings faster than text.
- **Documentation and ADRs travel with the model** — update Structurizr documentation sections and write ADRs for significant decisions. The Structurizr UI is the single source of truth for architecture understanding.
- **Complete coverage** — every new code file must map to a component.

#### Never

- Skip context extraction — always use the Context skill
- Skip alternative exploration — always present options
- Create multi-component implementation tasks
- Add elements without relationships
- Modify the workspace without MCP validation
- Write code (this agent designs, not implements)
- Produce an implementation spec without user approval on the design
- Ignore the best practices config

---

## 8. Skills

Two skills that support the agents. All model operations go through MCP tools.

### 8.1 pathfinder-context

**Purpose**: Extract the relevant architectural slice for a given input. Runs as a **subagent in its own context** to avoid loading the full workspace into the calling agent's context.

**Invoked by**: Architect Agent (primary), or any agent/skill that needs architectural context.

**Input**: A query — either a business requirement (text, with optional attached files/mocks) or a file path.

**Procedure**:
1. Read the full workspace via MCP "Read workspace" or "Parse DSL" for JSON.
2. Analyze the input to extract key signals: technologies mentioned, data entities, user-facing features, integration points, file paths referenced.
3. Match signals against the workspace:
   - Search element descriptions and documentation sections
   - Search relationship descriptions (e.g., requirement mentions "notifications" → find relationships to messaging systems)
   - Match technology tags
   - Match code paths (if input references specific files)
4. Extract the relevant slice:
   - Matched components and their parent containers/systems
   - Direct relationships (inbound and outbound) for matched elements
   - Code paths for matched components
   - Relevant documentation sections
   - Neighboring components that share relationships with matched elements
5. Return a structured summary to the calling agent:
   - Affected components (name, C4 path, description, technology, code paths)
   - Relevant relationships (source → target, description, protocol)
   - Relevant documentation excerpts
   - Components that might be impacted indirectly (1 hop away)

**Output**: Compact architectural context. The calling agent never sees the full workspace JSON.

### 8.2 pathfinder-review

**Purpose**: Interactive review loop with visualization. Used after Init Agent builds the model, and after Architect Agent makes changes.

**Procedure**:
1. Ensure infrastructure is running: `pathfinder start`.
2. Tell user to open `http://localhost:8080`.
3. Walk through each C4 level:
   - **System Context**: "Here's the big picture — your system and its external dependencies. Correct?"
   - **Containers**: "These are the deployable units. Does this match how you deploy?"
   - **Components** (per container): "These are the logical modules inside [container]. Missing anything?"
   - **Documentation**: "Here's the written documentation. Accurate?"
4. Collect corrections from user at each level.
5. If corrections needed: update via MCP "Update workspace", validate, re-render.
6. Repeat until user approves all levels.

**Output**: User-validated workspace at all C4 levels.

---

## 9. CLI (Thin)

Minimal CLI — only infrastructure and install operations. All model operations go through MCP.

### Module Structure

```
pathfinder/
  __init__.py
  cli/
    __init__.py
    main.py             # Click CLI entry point
    init_cmd.py         # Initialize .pathfinder/ with config and practices.md
    install_cmd.py      # Copy skills + agents to target project
    docker_cmd.py       # Docker lifecycle for Server + MCP
  skills/               # 2 skill SKILL.md files
  agents/               # 2 agent .md files
```

### Commands

| Command | Purpose |
|---------|---------|
| `pathfinder init --name NAME` | Create `.pathfinder/` with config.yaml, practices.md, template DSL |
| `pathfinder install` | Copy skills + agents to `.claude/`, configure MCP server in Claude Code settings |
| `pathfinder start [--port PORT]` | Start Structurizr Server + MCP Docker containers |
| `pathfinder stop` | Stop both containers |
| `pathfinder info` | Show project summary (workspace status, container status) |

**Note**: No model commands. All model operations go through MCP. The CLI is purely infrastructure.

---

## 10. Distribution Model

### Installation

```bash
pip install git+https://github.com/<org>/pathfinder.git   # Install from git repo
cd /path/to/my-project
pathfinder install                        # Copy skills + agents + MCP config to .claude/
pathfinder init --name my-project         # Create .pathfinder/ with template + practices
pathfinder start                          # Start Docker containers
```

### What Gets Installed

Into `.claude/`:
- 2 skills: `.claude/skills/pathfinder-{context,review}/SKILL.md`
- 2 agents: `.claude/agents/{init-agent,system-architect}.md`
- MCP server configuration in Claude Code settings (Structurizr MCP connection)

Into `.pathfinder/`:
- `workspace.dsl` — empty template with default styles
- `config.yaml` — project name, settings
- `practices.md` — default architectural best practices

### Prerequisites

- Docker (for Structurizr Server and MCP server)
- Python >= 3.12
- Node.js (for `npx mcp-remote` bridge to MCP server)

---

## 11. Dependencies

```toml
[project]
name = "pathfinder"
version = "0.2.0"
requires-python = ">=3.12"
dependencies = [
    "click>=8.1",       # CLI framework
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]
```

Single runtime dependency: `click`. Everything else is handled by:
- Structurizr MCP (Docker)
- Structurizr Server (Docker)
- Python stdlib (`json`, `pathlib`, `subprocess` for Docker commands)

---

## 12. Implementation Phases

### Phase 0: Cleanup

Delete all v1 code from the branch (tag preserves it).

- Remove `pathfinder/types.py`, `pathfinder/core/`, `pathfinder/cli/`, `pathfinder/skills/`, `pathfinder/agents/`
- Remove `tests/`
- Remove `.claude/skills/`, `.claude/agents/`
- Keep and update: `pyproject.toml`, `CLAUDE.md`, `README.md`, `docs/`

### Phase 1: CLI

The thin infrastructure layer.

1. `pathfinder/cli/main.py` — Click entry point
2. `pathfinder/cli/init_cmd.py` — create `.pathfinder/`, write config.yaml, practices.md, template DSL
3. `pathfinder/cli/install_cmd.py` — copy skills + agents + MCP config
4. `pathfinder/cli/docker_cmd.py` — `start`, `stop` for Server + MCP containers
5. CLI tests with CliRunner

**Exit criteria**: `pathfinder init && pathfinder start` launches working Structurizr Server + MCP.

### Phase 2: Skills

Write the 2 skills.

1. `pathfinder/skills/pathfinder-context/SKILL.md`
2. `pathfinder/skills/pathfinder-review/SKILL.md`

**Exit criteria**: Skills reference correct MCP tools and CLI commands. Procedures are clear and complete.

### Phase 3: Agents

Write the 2 agents.

1. `pathfinder/agents/init-agent.md`
2. `pathfinder/agents/system-architect.md`
3. Default `practices.md` content
4. Implementation spec template

**Exit criteria**: Agent workflows are coherent, reference the correct skills, and produce defined outputs.

### Phase 4: Integration + Docs

1. Update `CLAUDE.md` for v2
3. Update `README.md` with new workflow
4. Update `pyproject.toml`
5. End-to-end test: init → start → Init Agent discovers architecture → review

**Exit criteria**: `pip install git+... && pathfinder install && pathfinder init && pathfinder start` works. MCP server is configured in Claude Code. Init agent can discover architecture and produce a validated workspace.

---

## 13. DSL Template

The template generated by `pathfinder init`:

```
workspace "${project_name}" "Architecture model for ${project_name}" {

    !identifiers hierarchical

    model {
        # Define people (actors) who use the system
        # user = person "User" "Description"

        # Define the software system
        # mySystem = softwareSystem "System Name" "Description" {
        #     container1 = container "Container" "Description" "Technology" {
        #         component1 = component "Component" "Description" "Technology" {
        #             properties {
        #                 code_path "src/**/*.py"
        #             }
        #         }
        #     }
        # }

        # Define relationships
        # user -> mySystem "Uses"
        # mySystem.container1 -> mySystem.container2 "Calls" "HTTPS"
    }

    views {
        # Views are generated by the init agent

        styles {
            # Default C4 styles (Software System, Container, Component, Person, Database, External)
        }
    }
}
```

Default styles follow standard Structurizr C4 conventions and are generated by the Init Agent.

---

## 14. Example Workflows

### Onboarding a New Project

```
1. pip install git+https://github.com/<org>/pathfinder.git
2. cd my-project
3. pathfinder install              # Skills + agents + MCP config into .claude/
4. pathfinder init --name "My Project"
5. pathfinder start                # Starts Structurizr Server + MCP
6. (Recommended) Run Claude /init  # User runs this themselves for codebase context
7. Start fresh context session     # Clean context for architecture work
8. Invoke Init Agent               # Scans codebase, builds C4 model + docs via MCP
9. Review skill runs               # Walk through each C4 level at :8080
10. Iterate until the model is accurate and all files mapped
11. Commit .pathfinder/ to git
```

### Designing a New Feature

```
1. User: "We need to add a notification service. Here's the product spec [attaches doc]
   and the UI mock [attaches screenshot]."
2. Architect Agent activates
3. Context skill (subagent) reads workspace → extracts relevant slice:
   - Current messaging components, API relationships, user-facing containers
4. Agent reads practices.md (e.g., "async communication between containers")
5. Agent asks: "Should notifications be push, email, or both? The current system
   has no messaging infrastructure — we'd need to add one."
6. User: "Both. Use a message queue."
7. Agent proposes 2 options:
   A. New Notification container with embedded queue
   B. Separate Message Queue container + Notification container
   Recommends B (loose coupling, independent scaling)
8. Before/after Mermaid diagrams shown
9. User approves option B
10. Agent updates workspace via MCP, validates
11. Agent writes implementation spec to docs/specs/2026-04-14-notifications.md
```

