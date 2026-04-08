---
name: pathfinder-define
description: Architecture-first design — decompose a business requirement into components, contracts, and data flows
---

# pathfinder-define

> Architecture-first design: decompose a business requirement into components, contracts, and data flows.

## When to use

- Greenfield projects starting from scratch
- Adding a new capability or feature area to an existing project
- Redesigning a subsystem that needs new architectural boundaries

## Inputs

| Input | Required | Description |
|---|---|---|
| Business description | Yes | What the system (or new capability) needs to do, in business terms |
| Existing pathfinder project | No | If extending an existing project, the `.pathfinder/` must already exist |

## Prerequisites

- `pathfinder` CLI is installed and on PATH
- For greenfield: nothing else needed
- For extending: `.pathfinder/` initialized and current components mapped

---

## Procedure

### Phase 1: Understand the requirement

**Step 1 -- Capture the business description**

Ask the user to describe what they need in business language. Do not ask for technical details yet. Capture:

- What problem does this solve?
- Who are the users/actors?
- What are the key operations or workflows?
- What are the external systems involved?

Record this as the raw requirement.

**Step 2 -- Identify nouns and verbs**

From the business description, extract:

- **Nouns** -- these become candidate entities, data stores, or components
- **Verbs** -- these become candidate operations, flows, or API endpoints
- **Actors** -- these become system boundaries (user-facing vs internal vs external)

Present this extraction to the user:

> From your description, I identified:
> - **Entities:** users, orders, products, payments
> - **Operations:** browse catalog, place order, process payment, send confirmation
> - **Actors:** customer (browser), admin (dashboard), payment gateway (external)
> - **Boundaries:** frontend, API, order processing, payment integration, notification service
>
> Does this capture the key concepts? What am I missing?

**Step 3 -- Check existing architecture (if extending)**

If this is an addition to an existing project:

```bash
pathfinder list
pathfinder flows
```

Identify which existing components are relevant. Ask:

- Does this new capability extend an existing component or create new ones?
- Are there existing data flows that this capability plugs into?
- Are there contracts that constrain how this new capability can behave?

```bash
pathfinder info <relevant-component>
pathfinder deps <relevant-component>
pathfinder dependents <relevant-component>
```

---

### Phase 2: Architectural decomposition

**Step 4 -- Define system boundaries**

Draw the boundary between your system and the outside world. Identify:

- **Inbound interfaces:** How does data enter the system? (HTTP API, CLI, message queue, scheduled job)
- **Outbound interfaces:** How does the system talk to external services? (API calls, database writes, event publishing)
- **User interfaces:** What do humans interact with? (Web UI, mobile app, admin console)

Each boundary is a candidate for a top-level component.

**Step 5 -- Decompose into components**

Apply these decomposition rules in order:

1. **Separate by deployment boundary** -- things that deploy independently are separate top-level components
2. **Separate by data ownership** -- if two areas own different data, they are different components
3. **Separate by rate of change** -- if two areas change for different business reasons, they are different components
4. **Separate by team ownership** -- if different people/teams own different areas, they are different components
5. **Group by cohesion** -- things that always change together belong in the same component

For each proposed component, define:

- **ID:** short, hierarchical identifier (e.g., `api/orders`, `core/payments`)
- **Type:** service, module, library, api, store, ui
- **Description:** one sentence explaining its responsibility
- **Responsibility boundary:** what it owns and what it does NOT own

Present the decomposition:

```
Proposed components:

ui/storefront           (ui)      -- Customer-facing product browsing and checkout
api/gateway             (api)     -- HTTP API handling all client requests
core/catalog            (module)  -- Product catalog management and search
core/orders             (module)  -- Order lifecycle: creation, validation, fulfillment
core/payments           (module)  -- Payment processing orchestration
data/products           (store)   -- Product data persistence
data/orders             (store)   -- Order data persistence
infra/payment-gateway   (module)  -- External payment provider integration
infra/notifications     (module)  -- Email and push notification dispatch
```

Ask the user to validate. Iterate until they confirm.

**Step 6 -- Define contracts between components**

For every pair of components that interact, define the contract:

- **What data crosses the boundary** (inputs and outputs)
- **What format** (types, schemas)
- **What guarantees** (error handling, idempotency, ordering)

Contracts flow from the component decomposition -- if you defined the boundaries well, the contracts are the data that must cross those boundaries.

Present contracts:

```
Contracts:

api/gateway -> core/orders
  Input:  CreateOrderRequest { items: [{productId, quantity}], customerId }
  Output: OrderResponse { orderId, status, total } | ValidationError

core/orders -> core/payments
  Input:  PaymentRequest { orderId, amount, currency, method }
  Output: PaymentResult { success, transactionId } | PaymentError

core/orders -> infra/notifications
  Input:  NotificationRequest { type: "order_confirmed", recipient, data }
  Output: void (fire and forget)
```

Ask the user to review contracts. These are the most important part -- they define how components communicate.

---

### Phase 3: Define data flows

**Step 7 -- Trace end-to-end flows**

For each key user operation identified in Step 2, trace the data flow through the components:

```
Flow: "Customer places an order"

  ui/storefront
    -> api/gateway          [CreateOrderRequest]
    -> core/orders          [validated order]
    -> core/payments        [PaymentRequest]
    -> infra/payment-gw     [provider API call]
    -> core/orders          [PaymentResult -> update order status]
    -> infra/notifications  [send confirmation email]
    -> api/gateway          [OrderResponse]
    -> ui/storefront        [display confirmation]
```

Present each flow to the user. Verify the sequence makes sense.

**Step 8 -- Identify missing components**

Tracing flows often reveals gaps:

- A flow requires data transformation that no component owns -- add a component
- Two flows share logic that is duplicated -- extract a shared component
- A flow crosses too many components -- consider merging some

Revise the component hierarchy if needed. Go back to Step 5 if the changes are significant.

---

### Phase 4: Create in pathfinder

**Step 9 -- Initialize (greenfield only)**

```bash
pathfinder init <project-name>
```

**Step 10 -- Create components**

```bash
pathfinder add ui/storefront --type ui --desc "Customer-facing product browsing and checkout"
pathfinder add api/gateway --type api --desc "HTTP API handling all client requests"
pathfinder add core/catalog --type module --desc "Product catalog management and search"
pathfinder add core/orders --type module --desc "Order lifecycle: creation, validation, fulfillment"
pathfinder add core/payments --type module --desc "Payment processing orchestration"
pathfinder add data/products --type store --desc "Product data persistence"
pathfinder add data/orders --type store --desc "Order data persistence"
pathfinder add infra/payment-gw --type module --desc "External payment provider integration"
pathfinder add infra/notifications --type module --desc "Email and push notification dispatch"
```

**Step 11 -- Set parent relationships**

```bash
pathfinder set ui/storefront parent ui
pathfinder set core/catalog parent core
pathfinder set core/orders parent core
pathfinder set core/payments parent core
pathfinder set data/products parent data
pathfinder set data/orders parent data
pathfinder set infra/payment-gw parent infra
pathfinder set infra/notifications parent infra
```

Create parent components first if they do not exist:

```bash
pathfinder add ui --type module --desc "User interface layer"
pathfinder add core --type module --desc "Core business logic"
pathfinder add data --type module --desc "Data persistence layer"
pathfinder add infra --type module --desc "Infrastructure and external integrations"
```

**Step 12 -- Set contracts**

```bash
pathfinder set api/gateway contract.inputs "HTTP requests from clients (REST JSON)"
pathfinder set api/gateway contract.outputs "HTTP responses (JSON), validation errors"

pathfinder set core/orders contract.inputs "CreateOrderRequest, CancelOrderRequest, GetOrderQuery"
pathfinder set core/orders contract.outputs "OrderResponse, OrderList, ValidationError"

pathfinder set core/payments contract.inputs "PaymentRequest { orderId, amount, currency, method }"
pathfinder set core/payments contract.outputs "PaymentResult { success, transactionId } | PaymentError"

pathfinder set infra/notifications contract.inputs "NotificationRequest { type, recipient, data }"
pathfinder set infra/notifications contract.outputs "void (fire and forget)"
```

**Step 13 -- Add data flows**

```bash
pathfinder flow-add place-order api/gateway -> core/orders -> core/payments -> infra/payment-gw "Customer places order: API receives request, order logic validates, payment processes"
pathfinder flow-add order-confirm core/orders -> infra/notifications "Order confirmed: send email notification to customer"
pathfinder flow-add browse-catalog ui/storefront -> api/gateway -> core/catalog -> data/products "Customer browses products"
```

**Step 14 -- Apply standards (if any)**

If the project has coding standards or patterns:

```bash
pathfinder standards
```

Review existing standards and apply them to new components where applicable.

---

### Phase 5: Validate and summarize

**Step 15 -- Validate**

```bash
pathfinder validate
```

Fix any issues.

**Step 16 -- Review the design**

```bash
pathfinder show
pathfinder flows
```

Present a summary to the user:

> Architecture defined. Created **N** components with **M** data flows.
>
> Key design decisions:
> - [list the main decomposition choices and why]
>
> Next steps:
> - Use `pathfinder-implement` to start building components
> - Use `pathfinder-navigate` to explore the architecture
> - Components are ready for task assignment

---

## Iteration protocol

This skill is inherently iterative. At each phase, present your work to the user and incorporate feedback before moving on. Common iteration patterns:

| User says | Action |
|---|---|
| "These two should be one component" | Merge the components, update flows |
| "This component does too much" | Split it, define the boundary between the new components |
| "What about [feature X]?" | Trace a new flow for feature X, add components if needed |
| "The contract is wrong" | Update the contract, check if downstream components are affected |
| "This flow is too complex" | Simplify -- can you reduce hops? Can you merge components? |

## Anti-patterns to avoid

- **One component per file** -- components should represent architectural boundaries, not individual files
- **Mirroring the directory structure** -- directories are an implementation detail; components represent logical architecture
- **Skipping contracts** -- contracts are the most valuable part; without them, components are just labels
- **Defining flows last** -- flows should drive component discovery, not the other way around
- **Over-decomposition** -- start coarse, split when you have a reason; 5-15 components is typical for a medium system

## Output

When this skill completes, the project will have:

- Component hierarchy defined with clear boundaries
- Contracts specified for all component interactions
- Data flows traced for all key user operations
- Validation passing
- A coherent architectural design ready for implementation
