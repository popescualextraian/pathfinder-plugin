# pathfinder-navigate

> Token-efficient orientation: load only the relevant slice of the architecture graph for a development task.

## When to use

- Starting any development task and need to understand the affected area
- Given a file and need to know what component it belongs to
- Need to understand what a change will affect before making it
- Onboarding to an unfamiliar part of the codebase

## Inputs

| Input | Required | Description |
|---|---|---|
| Task description OR file path | Yes | Either "I need to change X" or a specific file path |

## Prerequisites

- `pathfinder` CLI is installed and on PATH
- `.pathfinder/` is initialized with components and mappings

---

## Procedure

### Route A: Starting from a file path

Use this route when you have a specific file (e.g., the user says "I need to modify `src/services/order.py`").

**Step 1 -- Find the owning component**

```bash
pathfinder mapped src/services/order.py
```

This returns the component that owns this file. If the file is unmapped:

```bash
pathfinder unmapped
```

Check if the file should be mapped to an existing component, or if a new component is needed. If unmapped, inform the user and suggest running `pathfinder-discover` or manually mapping the file.

**Step 2 -- Load the component spec**

```bash
pathfinder info <component-id>
```

This gives you the component's description, type, contracts, and metadata. Record:

- What this component is responsible for
- Its input contract (what data it accepts)
- Its output contract (what data it produces)

**Step 3 -- Load connected components**

Find what this component depends on and what depends on it:

```bash
pathfinder deps <component-id>
pathfinder dependents <component-id>
```

This gives you the immediate neighbors in the architecture graph. For each neighbor, load a brief summary:

```bash
pathfinder info <dependency-id>
```

You do NOT need to load the full spec of every neighbor. Load only:
- The component description (to understand what it does)
- Its contracts (to understand the interface)

**Step 4 -- Load relevant data flows**

```bash
pathfinder flows <component-id>
```

This shows all flows that pass through this component. For the task at hand, identify which flows are relevant.

If you need to trace a specific flow end-to-end:

```bash
pathfinder trace <flow-name>
```

---

### Route B: Starting from a task description

Use this route when you have a task like "add email verification to user registration."

**Step 1 -- Search for relevant components**

```bash
pathfinder search "user registration"
pathfinder search "email"
pathfinder search "verification"
```

If search does not find relevant results, try:

```bash
pathfinder list
```

And scan component names and descriptions manually.

**Step 2 -- Identify the primary component**

From the search results, determine which component is the primary owner of this task. The primary component is the one whose responsibility most directly matches the task.

```bash
pathfinder info <candidate-component>
```

Check: does this component's description and contracts match the task? If yes, this is your primary component. If not, try the next candidate.

**Step 3 -- Identify secondary components**

The task may touch multiple components. Load dependencies and dependents:

```bash
pathfinder deps <primary-component>
pathfinder dependents <primary-component>
pathfinder flows <primary-component>
```

Determine which connected components will also be affected by this task. Load their specs.

**Step 4 -- Check for cross-cutting concerns**

Some tasks span multiple unrelated components. If your task involves:

- Adding a new flow: trace the flow path to find all affected components
- Changing a contract: find all components that depend on that contract
- Adding a cross-cutting feature (logging, auth): check `pathfinder standards` for existing patterns

```bash
pathfinder dependents <component-with-changed-contract>
```

---

### Route C: Exploration (no specific target)

Use this route when the user just wants to understand the architecture.

**Step 1 -- Show the component tree**

```bash
pathfinder show
```

**Step 2 -- Show all flows**

```bash
pathfinder flows
```

**Step 3 -- Let the user drill down**

Ask: "Which area would you like to explore?" Then use `pathfinder info`, `pathfinder deps`, and `pathfinder children` to drill into that area.

---

## Presenting context

After loading the relevant information, present it in this structured format:

```
== Navigation Context ==

Primary component: core/orders
  Type: module
  Description: Order lifecycle: creation, validation, fulfillment
  Contracts:
    In:  CreateOrderRequest, CancelOrderRequest, GetOrderQuery
    Out: OrderResponse, OrderList, ValidationError

Dependencies (what this component calls):
  - data/orders       -- persists order data
  - core/payments     -- processes payment for orders
  - infra/notifications -- sends order confirmation emails

Dependents (what calls this component):
  - api/gateway       -- routes HTTP requests to order logic

Relevant flows:
  - place-order: api/gateway -> core/orders -> core/payments -> infra/payment-gw
  - order-confirm: core/orders -> infra/notifications

Mapped files:
  - src/domain/orders/service.py
  - src/domain/orders/models.py
  - src/domain/orders/validators.py
```

## Token efficiency rules

This skill exists to avoid loading the entire architecture into context. Follow these rules:

1. **Never load all components at once** unless the user explicitly asks for an overview
2. **Load at most 2 levels deep** -- the primary component, its immediate neighbors, and stop
3. **Load contracts, not implementations** -- when examining a neighbor, you only need its interface, not its internals
4. **Prefer `info` over `show`** -- `info` gives you one component; `show` gives you everything
5. **Use `flows` with a component filter** -- only load flows that touch the component you care about
6. **Cache in conversation context** -- if you already loaded a component's info earlier in the conversation, do not reload it

## Decision points

| Situation | Decision |
|---|---|
| File is unmapped | Ask user: map it now, or proceed without mapping? |
| Task spans 4+ components | Focus on the 2-3 most central ones; mention the others as "also affected" |
| Component has no contracts defined | Load the mapped files to infer the interface; suggest defining contracts |
| Multiple candidates for primary component | Ask the user which aspect of the task they want to focus on first |
| Flow does not exist for this operation | Note this as a gap; suggest adding the flow with `pathfinder-define` |

## Output

This skill does not modify the pathfinder project. Its output is a focused context view that enables the next action:

- If the user wants to implement: hand off to `pathfinder-implement` with the loaded context
- If the user wants to understand impact: hand off to `pathfinder-check`
- If the user wants to add new components: hand off to `pathfinder-define`
