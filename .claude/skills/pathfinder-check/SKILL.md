---
name: pathfinder-check
description: Architecture health check — detect drift between specs and code, analyze impact of proposed changes
---

# pathfinder-check

> Architecture health check: detect drift between specs and code, analyze impact of proposed changes.

## When to use

- Before making a significant change (impact analysis)
- After a sprint or batch of changes (health check)
- When something feels wrong -- tests pass but behavior is unexpected
- Periodic maintenance to keep specs and code in sync
- Before a release to verify architectural integrity

## Inputs

| Input | Required | Description |
|---|---|---|
| Mode | Yes | `health` (full check) or `impact` (analyze a proposed change) |
| Change description | If impact mode | What change is being proposed |
| Component scope | No | Limit check to specific component(s); defaults to entire project |

## Prerequisites

- `pathfinder` CLI is installed and on PATH
- `.pathfinder/` initialized with components, mappings, and flows

---

## Procedure: Health check mode

### Step 1 -- Run drift detection

```bash
pathfinder drift check
```

This compares the declared component specs against the actual codebase. Drift types:

| Drift type | Meaning |
|---|---|
| **Unmapped files** | Source files exist that no component owns |
| **Missing files** | Mapped files that no longer exist on disk |
| **Contract mismatch** | Implementation signatures do not match declared contracts |
| **Undeclared dependency** | Code imports a module owned by a component not listed as a dependency |
| **Orphan component** | Component has no mapped files and no children |

Record all drift findings.

### Step 2 -- Run validation

```bash
pathfinder validate
```

This checks structural integrity of the pathfinder project itself:

- All parent references point to existing components
- No circular parent relationships
- All flow references point to existing components
- Required fields are present on all components

Record all validation errors.

### Step 3 -- Check for unmapped files

```bash
pathfinder unmapped
```

List all source files not owned by any component. Categorize them:

- **Should be mapped** -- assign to an existing component
- **Needs a new component** -- create a component for this area
- **Can be ignored** -- generated files, build artifacts, configs that do not need mapping

### Step 4 -- Check flow coverage

```bash
pathfinder flows
```

For each major user operation in the system, verify that a flow exists. Gaps indicate:

- A feature was added without updating the architecture
- A flow was deleted or broken

Also check for flows that reference components in an order that does not match the actual call graph.

### Step 5 -- Spot check contracts

For each component that has contracts defined, verify that the actual implementation matches:

```bash
pathfinder info <component-id>
```

Read the contract, then check the mapped files:

```bash
pathfinder mapped <component-id>
```

Look at the actual function signatures, API endpoints, or message schemas and compare to the declared contract. Flag mismatches.

### Step 6 -- Compile the health report

Present findings in this format:

```
== Architecture Health Report ==

Overall status: [HEALTHY | NEEDS ATTENTION | UNHEALTHY]

Drift findings:
  [OK] No drift detected
  -- or --
  [DRIFT] 3 unmapped files in src/utils/
  [DRIFT] core/payments contract mismatch: declared output "PaymentResult"
          but implementation returns "PaymentResponse"
  [DRIFT] Undeclared dependency: core/orders imports from infra/cache
          (infra/cache not listed as a dependency of core/orders)

Validation:
  [OK] All structural checks pass
  -- or --
  [ERROR] Component "legacy/old-module" has no mapped files and no children
  [WARN] Flow "checkout" references component "core/discounts" which has no contract

Unmapped files: 3
  - src/utils/helpers.py
  - src/utils/constants.py
  - scripts/migrate.py

Flow coverage:
  [OK] 5 flows defined, all reference valid components
  -- or --
  [GAP] No flow covers the "password reset" operation
  [STALE] Flow "old-checkout" references removed component "legacy/cart"

Recommendations:
  1. Map src/utils/ files to a "shared/utils" component or create one
  2. Update core/payments contract: rename "PaymentResult" to "PaymentResponse"
     -- OR -- rename the implementation class to match the spec
  3. Add infra/cache as a dependency of core/orders
  4. Remove orphan component "legacy/old-module" or map files to it
```

### Step 7 -- Triage recommendations

For each finding, recommend one of:

| Finding | Recommendation |
|---|---|
| Spec is outdated, code is correct | **Update the spec** -- the architecture evolved and the spec should follow |
| Code diverged from a deliberate design | **Fix the code** -- the spec represents an intentional decision |
| New files have no owner | **Map them** or **create a new component** |
| Orphan component | **Remove it** or **map files to it** |
| Missing flow | **Add the flow** using pathfinder-define |
| Undeclared dependency | **Add the dependency** or **refactor to remove it** |

Present these recommendations to the user and let them decide. Do not auto-fix.

---

## Procedure: Impact analysis mode

Use this mode when the user says "I want to change X" and wants to understand the blast radius before proceeding.

### Step 1 -- Identify the affected component(s)

If the user specifies a file:

```bash
pathfinder mapped <file-path>
```

If the user specifies a component:

```bash
pathfinder info <component-id>
```

If the user describes a change in general terms, use pathfinder-navigate (Route B) to locate the relevant components.

### Step 2 -- Map the direct impact

Find everything directly connected to the affected component:

```bash
pathfinder deps <component-id>
pathfinder dependents <component-id>
```

Categorize the impact:

- **Dependents** are components that CALL this one. If you change this component's output contract, all dependents are affected.
- **Dependencies** are components this one CALLS. If you change this component's input requirements, dependencies may need updates.

### Step 3 -- Trace flow impact

```bash
pathfinder flows <component-id>
```

For each flow that passes through the affected component:

```bash
pathfinder trace <flow-name>
```

Every component in these flows is potentially affected. The further a component is from the change point, the less likely it is actually impacted -- but it should still be checked.

### Step 4 -- Analyze contract changes

If the proposed change modifies a contract (inputs or outputs), this is the highest-impact scenario:

```bash
pathfinder dependents <component-id>
```

For each dependent, check: does it rely on the part of the contract that is changing?

```bash
pathfinder info <dependent-id>
```

Load the dependent's spec and determine if the contract change breaks its assumptions.

### Step 5 -- Check for transitive impact

Some changes cascade. If changing component A's output contract breaks component B, and B's fix changes B's output contract, then C (which depends on B) is also affected.

Trace the cascade:

```bash
pathfinder dependents <component-B>
```

Continue until the cascade stops (components that are not affected by the upstream change).

### Step 6 -- Compile the impact report

```
== Impact Analysis ==

Proposed change: "Add discount support to order creation"
Primary component: core/orders

Direct impact:
  - api/gateway          -- needs to accept discount codes in CreateOrderRequest
  - core/payments        -- payment amount will change based on discounts
  - data/orders          -- order model needs discount fields

Flow impact:
  - place-order flow     -- discount validation added between gateway and orders
  - browse-catalog flow  -- not affected

Contract changes required:
  - core/orders input:   add "discountCode" to CreateOrderRequest
  - core/orders output:  add "discount" and "subtotal" to OrderResponse
  - core/payments input: amount field now reflects discounted total (no schema change)

New components needed:
  - core/discounts       -- discount rule engine (new component)

Cascade:
  - api/gateway -> already identified (direct dependent)
  - ui/storefront -> needs to send discount code (transitive via api/gateway)

Risk assessment:
  - LOW:  data/orders schema change (additive, backward compatible)
  - MED:  api/gateway contract change (clients must update)
  - HIGH: core/payments behavior change (payment amount changes silently)

Recommendation:
  1. Create core/discounts component first (use pathfinder-define)
  2. Update core/orders contract to include discount fields
  3. Implement core/discounts, then update core/orders
  4. Update api/gateway to pass discount codes through
  5. Verify core/payments handles discounted amounts correctly
  6. Update ui/storefront to collect discount codes
```

---

## Running a scoped check

To check only specific components instead of the entire project:

```bash
pathfinder drift check <component-id>
pathfinder info <component-id>
pathfinder deps <component-id>
pathfinder dependents <component-id>
pathfinder flows <component-id>
```

This is useful for:
- Checking only the area you just changed
- Verifying a single component after implementation
- Quick spot-checks during development

---

## Decision points

| Situation | Decision |
|---|---|
| Drift found but code is working fine | Likely the spec is outdated -- recommend updating the spec |
| Contract mismatch on a widely-used component | High risk -- recommend careful migration, not a quick fix |
| Unmapped test files | Map to the same component as the code they test |
| Circular dependency detected | Architecture smell -- recommend refactoring to break the cycle |
| Impact analysis shows 10+ affected components | The change is too broad -- recommend decomposing into smaller changes |
| No flows exist at all | The project needs flow definitions -- suggest running pathfinder-define |

## Output

**Health check mode** produces:
- A categorized list of all drift, validation errors, and gaps
- Prioritized recommendations for each finding
- An overall health status

**Impact analysis mode** produces:
- A list of all affected components (direct and transitive)
- Required contract changes
- New components needed
- A risk assessment
- A recommended implementation order
