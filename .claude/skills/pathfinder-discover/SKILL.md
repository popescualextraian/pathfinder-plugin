---
name: pathfinder-discover
description: Brownfield discovery — analyze an existing codebase and produce a full pathfinder component map
---

# pathfinder-discover

> Brownfield discovery: analyze an existing codebase and produce a full pathfinder component map.

## When to use

- Onboarding a new repository into pathfinder
- Joining an existing project and need to understand its architecture
- Migrating from ad-hoc development to architecture-driven development

## Inputs

| Input | Required | Description |
|---|---|---|
| Project root | Yes | Path to the codebase to analyze |
| Project name | Yes | Short identifier for the project |
| Tech hints | No | Known framework/language if you want to skip detection |

## Prerequisites

- `pathfinder` CLI is installed and on PATH
- The codebase is accessible at the given root path

---

## Procedure

### Phase 1: Initialize and analyze

**Step 1 -- Initialize pathfinder**

```bash
cd <project-root>
pathfinder init <project-name>
```

This creates the `.pathfinder/` directory. If it already exists, skip this step.

**Step 2 -- Detect project type**

Examine the project root for technology indicators. Check for the presence of these files (not an exhaustive list -- adapt to what you find):

| File / pattern | Indicates |
|---|---|
| `package.json` | Node.js / JavaScript / TypeScript |
| `requirements.txt`, `pyproject.toml`, `setup.py` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml`, `build.gradle` | Java / JVM |
| `Dockerfile`, `docker-compose.yml` | Containerized services |
| `Makefile` | Build system present |
| `.env`, `.env.example` | Environment configuration |

Record the detected stack. This influences how you interpret directory structure in the next step.

**Step 3 -- Map the directory structure**

Read the top-level directory listing and one level down. Identify structural patterns:

- **Layered architecture:** directories like `controllers/`, `services/`, `models/`, `repositories/`
- **Feature/domain modules:** directories like `users/`, `orders/`, `payments/`, `auth/`
- **Monorepo packages:** directories like `packages/`, `apps/`, `libs/`
- **Frontend structure:** directories like `components/`, `pages/`, `views/`, `hooks/`, `stores/`
- **Infrastructure:** directories like `infra/`, `deploy/`, `terraform/`, `k8s/`

**Step 4 -- Analyze entry points and imports**

Find the main entry points of the application:

- `main.py`, `app.py`, `manage.py` (Python)
- `index.ts`, `app.ts`, `server.ts`, `main.ts` (Node/TS)
- `main.go`, `cmd/` (Go)
- `src/main.rs` (Rust)
- `Application.java`, classes with `public static void main` (Java)

Trace the top-level imports/dependencies from entry points to understand how the codebase is wired together. This reveals the actual dependency graph, not just the directory layout.

**Step 5 -- Identify data boundaries**

Look for:
- API route definitions (REST endpoints, GraphQL schemas, gRPC protos)
- Database models / schemas / migrations
- Message queue producers and consumers
- External service clients (HTTP clients, SDK wrappers)
- Configuration / environment variable usage

These are the boundaries where data flows between components.

---

### Phase 2: Propose component hierarchy

**Step 6 -- Draft the component tree**

Based on your analysis, draft a component hierarchy. Follow these principles:

1. **Top-level components** represent major architectural boundaries (services, packages, bounded contexts)
2. **Second-level components** represent functional areas within a boundary
3. **Leaf components** represent concrete modules that own code files
4. Every source file should be assignable to exactly one leaf component

Present the proposed hierarchy to the user in this format:

```
Proposed component hierarchy for <project-name>:

<root>
  api/                          -- HTTP API layer
    api/routes                  -- Route definitions and handlers
    api/middleware               -- Auth, logging, error handling
  core/                         -- Business logic
    core/users                  -- User management domain
    core/orders                 -- Order processing domain
  data/                         -- Data access layer
    data/models                 -- Database models
    data/repositories           -- Data access abstractions
  infra/                        -- Infrastructure and config
    infra/config                -- App configuration
    infra/external              -- External service clients

Data flows identified:
  api/routes -> core/users      -- HTTP request dispatched to user logic
  core/users -> data/models     -- Business logic persists via models
  core/orders -> infra/external -- Orders call external payment service
```

**Step 7 -- User validation**

Ask the user:

> Does this component hierarchy match your understanding of the codebase? Specifically:
> 1. Are there components that should be merged or split?
> 2. Are there areas of the codebase I missed?
> 3. Do the data flows look correct?
> 4. Are the component names clear and meaningful?

Incorporate their feedback before proceeding. This is iterative -- go back and forth until the user confirms the hierarchy.

---

### Phase 3: Create components in pathfinder

**Step 8 -- Create top-level components**

For each top-level component:

```bash
pathfinder add <component-id> --type <type> --desc "<description>"
```

Component types to use:
- `service` -- a deployable unit or major bounded context
- `module` -- a logical grouping within a service
- `library` -- shared/reusable code
- `api` -- an API surface (REST, GraphQL, gRPC)
- `store` -- a data store (database, cache, queue)
- `ui` -- a user interface component or page

Example:

```bash
pathfinder add api --type api --desc "HTTP API layer handling all inbound requests"
pathfinder add core --type module --desc "Core business logic and domain rules"
pathfinder add data --type module --desc "Data access layer and persistence"
pathfinder add infra --type module --desc "Infrastructure, configuration, and external integrations"
```

**Step 9 -- Create child components**

For each child component, create it and set its parent:

```bash
pathfinder add api/routes --type module --desc "Route definitions and request handlers"
pathfinder set api/routes parent api

pathfinder add api/middleware --type module --desc "Cross-cutting middleware: auth, logging, errors"
pathfinder set api/middleware parent api
```

Repeat for all components in the hierarchy.

**Step 10 -- Set contracts on components**

For components that have clear inputs and outputs, define contracts:

```bash
pathfinder set api/routes contract.inputs "HTTP requests (method, path, headers, body)"
pathfinder set api/routes contract.outputs "HTTP responses (status, headers, JSON body)"

pathfinder set core/users contract.inputs "User commands: create, update, delete, query"
pathfinder set core/users contract.outputs "User entities, validation errors"
```

**Step 11 -- Map code files to components**

Map source files and directories to their owning components:

```bash
pathfinder map api/routes src/routes/
pathfinder map api/middleware src/middleware/
pathfinder map core/users src/domain/users/
pathfinder map data/models src/models/
```

After mapping, verify coverage:

```bash
pathfinder unmapped
```

If files remain unmapped, either assign them to existing components or create new components for them. Every source file should have an owner.

**Step 12 -- Add data flows**

Create flows for each identified data path:

```bash
pathfinder flow-add request-handling api/routes -> core/users "HTTP request dispatched to user domain logic"
pathfinder flow-add user-persistence core/users -> data/models "User domain persists entities to database"
pathfinder flow-add payment-integration core/orders -> infra/external "Order processing calls external payment gateway"
```

For multi-step flows, chain the hops:

```bash
pathfinder flow-add order-flow api/routes -> core/orders -> data/models -> infra/external "Full order processing pipeline"
```

---

### Phase 4: Validate

**Step 13 -- Run validation**

```bash
pathfinder validate
```

Fix any issues reported: missing parents, orphaned components, circular dependencies.

**Step 14 -- Review the result**

```bash
pathfinder list
pathfinder flows
pathfinder unmapped
```

Present a summary to the user:

> Discovery complete. Created **N** components with **M** data flows.
> **X** source files mapped, **Y** remain unmapped.
>
> Run `pathfinder show` to see the full component tree.
> Run `pathfinder info <component>` to inspect any component.

---

## Fallback strategies

### Flat codebase (no clear structure)

If the codebase has no meaningful directory structure (everything in one folder):

1. Use import analysis as the primary grouping signal
2. Cluster files by what they import and what imports them
3. Create components based on functional cohesion rather than directory layout
4. Map individual files rather than directories

### Microservices / monorepo

If the project contains multiple deployable services:

1. Create a top-level component per service
2. Run the discovery process for each service independently
3. Add cross-service data flows last, based on API calls, message queues, or shared databases

### Framework-heavy projects

For projects dominated by a framework (Rails, Django, Spring, Next.js):

1. Use the framework's conventions as the primary component structure
2. Add a `framework` or `platform` component for framework-specific code
3. Separate domain logic from framework glue where possible

### Legacy / tangled codebase

If dependencies are circular or boundaries are unclear:

1. Map what you can -- it does not need to be perfect on the first pass
2. Use `pathfinder validate` to surface problems
3. Flag tangled areas as candidates for refactoring
4. Mark components with a `status: needs-refactoring` note in their description

---

## Decision points

| Situation | Decision |
|---|---|
| File belongs to two components | Split the file or choose the primary owner; one file = one component |
| Shared utilities directory | Create a `shared` or `common` library component |
| Test files | Map tests to the same component as the code they test, or create a parallel `tests` child |
| Generated code | Exclude from mapping or create an `autogen` component with a note |
| Config files | Map to an `infra/config` component |
| CI/CD files | Optionally create a `ci` component, or leave unmapped |

## Output

When this skill completes, the project will have:

- `.pathfinder/` directory initialized
- Complete component hierarchy in YAML
- All source files mapped to components
- Data flows defined between components
- Validation passing with no errors
