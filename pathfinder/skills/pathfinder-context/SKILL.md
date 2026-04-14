# pathfinder-context

> Extract the relevant architectural slice from a Structurizr workspace for a given input. Runs as a subagent in its own fresh context so the calling agent never loads the full workspace JSON.

## When to use

- The Architect Agent needs architectural context before designing a solution
- Any agent needs to understand which components, relationships, and code paths are relevant to a task
- A business requirement or file path needs to be mapped to the architecture before decisions are made

## Inputs

| Input | Required | Description |
|---|---|---|
| Query | Yes | A business requirement (text, with optional attached files/mocks) or a file path |

## Prerequisites

- Structurizr MCP server is running and accessible
- A workspace exists with the project's C4 model
- The workspace uses `!identifiers hierarchical`

## Important

This skill runs as a **subagent in a fresh context**. The calling agent dispatches it, waits for the structured summary, and never sees the raw workspace JSON. This is intentional -- workspaces can be large and would consume the caller's context window.

---

## Procedure

### Step 1 -- Read the workspace

Retrieve the full workspace as JSON for structured access.

Use the MCP tool **"Parse DSL"** to get the workspace as JSON. This returns the complete model: software systems, containers, components, relationships, properties, documentation sections.

If "Parse DSL" is unavailable or fails, fall back to **"Read workspace"** to get the raw workspace content.

Store the JSON result in your working context. You will query it in the following steps.

### Step 2 -- Analyze the input and extract signals

Parse the query (business requirement, file path, or attached materials) to extract key signals. Identify every signal that could match against the architecture:

| Signal type | What to look for | Examples |
|---|---|---|
| **Technologies** | Languages, frameworks, protocols, infrastructure | "Python", "FastAPI", "PostgreSQL", "gRPC", "Redis" |
| **Data entities** | Domain objects, database tables, message types | "order", "payment", "user account", "notification" |
| **User-facing features** | Capabilities visible to end users | "checkout", "search", "login", "dashboard" |
| **Integration points** | External systems, APIs, third-party services | "Stripe", "SendGrid", "S3", "identity provider" |
| **File paths** | Specific source files or directories referenced in the input | `src/auth/handler.py`, `terraform/modules/vpc/` |
| **Operations** | Verbs indicating system behavior | "sends email", "processes payment", "validates token" |

Record all extracted signals. Be thorough -- missing a signal means missing a relevant component.

### Step 3 -- Match signals against the workspace

Search the workspace JSON systematically. For each signal, check these locations in the model:

**3a. Element descriptions and names**

Search `softwareSystems`, `containers`, and `components` for matches in:
- `name` -- direct name match
- `description` -- keyword match against element descriptions
- `technology` -- match technology signals against element technology fields

**3b. Relationship descriptions**

Search all `relationships` in the model. Relationship descriptions often reveal connections that element names alone do not. For example, if the requirement mentions "notifications", search for relationships with descriptions like "sends notification", "publishes message", "triggers email".

For each relationship, check:
- `description` -- keyword and semantic match
- `technology` -- protocol match (HTTP, gRPC, AMQP, SQL)
- `sourceId` and `destinationId` -- record both ends of any matched relationship

**3c. Technology tags**

Match technology signals against `tags` on elements. Structurizr elements carry tags that indicate their type and technology stack.

**3d. Code path matching (file path input)**

If the input references specific files, match them against `code_path` properties on components. Code paths use glob patterns.

Search element `properties` for:
- `code_path` -- primary glob pattern (e.g., `src/auth/**/*.py`)
- `code_path_2`, `code_path_3`, etc. -- additional patterns
- `code_hint` -- human-readable notes about file ownership
- `code_repo` -- repository name for multi-repo setups

To match a file path against a glob pattern: check if the file path falls within the pattern's scope. For example, `src/auth/handler.py` matches `src/auth/**/*.py`.

**3e. Documentation sections**

Search documentation sections attached to the workspace or to specific software systems. These contain architectural context, rationale, and decisions that may reference the query's domain.

Record all matched elements and the signal that matched them.

### Step 4 -- Extract the relevant slice

From the matched elements, build the complete relevant slice by expanding outward.

**4a. Matched components and their parents**

For every matched component, include:
- The component itself (name, description, technology, all properties)
- Its parent container
- Its parent software system

This gives the calling agent the full C4 path context (e.g., `mySystem.api.authModule`).

**4b. Direct relationships**

For every matched element, collect all relationships where the element is either source or destination:
- **Outbound**: relationships where this element is the source
- **Inbound**: relationships where this element is the destination

Include: source name, destination name, description, technology/protocol.

**4c. Code paths**

For every matched component, extract all code mapping properties:
- `code_path`, `code_path_2`, `code_path_3`, etc.
- `code_hint`
- `code_repo`

**4d. Documentation**

Extract relevant documentation sections -- those that mention matched elements or signals from Step 2.

**4e. Neighboring components (1 hop)**

For every matched element, find components that share a direct relationship with it but were not themselves matched. These are the "1-hop neighbors" -- components that might be indirectly impacted.

Include neighbors with reduced detail: name, C4 path, description, and the relationship that connects them to the matched element.

### Step 5 -- Return the structured summary

Compose the output in this format and return it to the calling agent:

```
== Architectural Context ==

Query: <original input, summarized>

Affected Components:
  - <name>
    C4 path: <system.container.component>
    Description: <element description>
    Technology: <technology>
    Code paths: <code_path values>
    Match reason: <which signal matched and where>

  - <name>
    ...

Relevant Relationships:
  - <source name> -> <target name>
    Description: <relationship description>
    Protocol: <technology>

  - ...

Documentation:
  - <section title>: <relevant excerpt>
  - ...

Indirectly Impacted (1 hop):
  - <name> (<system.container.component>)
    Description: <description>
    Connected via: <relationship description to/from a matched component>

  - ...
```

---

## Matching strategy

Signals will not always match exactly. Apply these rules:

| Situation | Strategy |
|---|---|
| Signal matches an element name exactly | Strong match -- always include |
| Signal matches a keyword in a description | Include if the keyword is domain-specific, not generic |
| Signal matches a relationship description but not an element | Include both ends of the relationship |
| Signal matches a technology tag | Include all elements with that technology |
| File path matches a code_path glob | Strong match -- always include |
| File path matches no code_path | Report the file as unmapped in the output |
| Signal has no matches anywhere | Report it as "no architectural coverage" in the output |
| Too many matches (10+ components) | Rank by match strength -- exact name > description keyword > technology tag > 1-hop neighbor. Return the top matches and note that the query is broad. |

## What to include vs. exclude

**Include**:
- All directly matched components with full detail
- All relationships connected to matched components
- All code paths on matched components
- Neighboring components (1 hop) with reduced detail
- Unmatched signals (so the caller knows what the architecture does not cover)

**Exclude**:
- Components beyond 1 hop from any match
- The raw workspace JSON (never return it -- the whole point is to avoid this)
- View definitions and styles (not relevant to architectural context)
- Layout information

## Output

A compact structured summary of the architectural slice relevant to the input query. The calling agent receives only what it needs to make decisions -- affected components, their relationships, code paths, documentation, and nearby components that might be indirectly impacted.
