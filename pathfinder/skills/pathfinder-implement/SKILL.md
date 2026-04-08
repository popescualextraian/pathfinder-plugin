# pathfinder-implement

> TDD implementation within component boundaries: load specs, write tests first, implement until green, map code back.

## When to use

- Component specs and contracts are defined and ready for implementation
- Adding new functionality to an existing component
- Implementing a task produced by the System Architect agent

## Inputs

| Input | Required | Description |
|---|---|---|
| Component ID | Yes | The pathfinder component to implement |
| Task description | Yes | What specifically to implement within this component |

## Prerequisites

- `pathfinder` CLI is installed and on PATH
- `.pathfinder/` initialized with components, contracts, and flows
- The target component exists and has contracts defined
- Testing framework is set up for the project

---

## Procedure

### Phase 1: Load component context

**Step 1 -- Load the component spec**

```bash
pathfinder info <component-id>
```

Record:
- Component description and responsibility boundary
- Input contract (what data this component accepts)
- Output contract (what data this component produces)
- Component type

**Step 2 -- Load contracts of connected components**

```bash
pathfinder deps <component-id>
pathfinder dependents <component-id>
```

For each dependency, load its contract:

```bash
pathfinder info <dependency-id>
```

You need these contracts to understand:
- What interfaces your component must call (dependencies)
- What interfaces your component must expose (for dependents)

**Step 3 -- Load applicable standards**

```bash
pathfinder standards
```

Check for standards that apply to this component's type or domain. Common standards include:
- Naming conventions
- Error handling patterns
- Logging requirements
- Authentication/authorization patterns

**Step 4 -- Review existing code (if any)**

```bash
pathfinder mapped <component-id>
```

This shows files currently mapped to this component. If there is existing code, read it to understand the current implementation state.

---

### Phase 2: RED -- Write failing tests

**Step 5 -- Derive test cases from contracts**

The component's contracts define what it must do. Each contract element produces test cases:

For **input contracts**, write tests that verify:
- The component accepts valid inputs and produces expected outputs
- The component rejects invalid inputs with appropriate errors
- Edge cases are handled (empty inputs, boundary values, nulls)

For **output contracts**, write tests that verify:
- The output matches the documented shape/type
- Error responses follow the documented format
- All documented output variants are reachable

For **data flows** passing through this component:
- The component correctly receives data from upstream
- The component correctly passes data to downstream
- The flow works end-to-end through this component

**Step 6 -- Write the test file**

Create the test file following project conventions. Place it alongside the component's code or in the project's test directory.

Structure tests by contract:

```
Test: <component-id>

  Group: Input contract
    - accepts valid CreateOrderRequest and returns OrderResponse
    - rejects CreateOrderRequest with missing items
    - rejects CreateOrderRequest with negative quantities
    - handles empty items list

  Group: Output contract
    - OrderResponse contains orderId, status, and total
    - ValidationError contains field-level error details

  Group: Dependencies
    - calls payment service with correct PaymentRequest
    - handles payment service failure gracefully
    - calls notification service after successful payment

  Group: Flow integration
    - processes place-order flow end-to-end
```

Mock or stub dependencies based on their contracts. Do NOT call real external services in unit tests.

**Step 7 -- Run tests and verify they fail**

```bash
# Run the test suite for this component (adapt to your test runner)
pytest tests/test_orders.py        # Python
npm test -- --testPathPattern=orders  # Node
go test ./internal/orders/...      # Go
```

All new tests should fail (RED). If any test passes, it either:
- Tests something that already exists (not a new test -- remove it or rename it)
- Is incorrectly written (fix the test)

If tests fail for the wrong reason (import errors, syntax errors), fix the test scaffolding until they fail for the right reason: the implementation does not exist yet.

---

### Phase 3: GREEN -- Implement until tests pass

**Step 8 -- Implement the component**

Write the implementation code to make the tests pass. Follow these rules:

1. **Respect the component boundary** -- only write code that belongs to this component's responsibility. If you find yourself implementing logic that belongs to another component, stop and note it.

2. **Honor contracts exactly** -- the inputs and outputs must match what the contracts specify. If the contract says `PaymentResult { success, transactionId }`, that is what your code must produce.

3. **Depend on interfaces, not implementations** -- when calling a dependency, code against its contract, not its internal implementation. Use dependency injection or similar patterns.

4. **Apply standards** -- follow any standards loaded in Step 3.

5. **Keep it minimal** -- implement only what is needed to make the tests pass. Do not add features that are not tested.

**Step 9 -- Run tests and iterate**

```bash
pytest tests/test_orders.py
```

If tests fail, read the failure output, fix the implementation, and re-run. Repeat until all tests pass (GREEN).

Do not modify tests to make them pass. If a test is genuinely wrong (you discover a contract issue), note the contract discrepancy and ask the user before changing the test.

---

### Phase 4: REFACTOR -- Clean up

**Step 10 -- Refactor the implementation**

With all tests green, review the code for:

- Duplication that can be extracted
- Unclear naming
- Overly complex logic that can be simplified
- Violations of project standards

Refactor while keeping tests green. Run tests after each refactoring step:

```bash
pytest tests/test_orders.py
```

**Step 11 -- Refactor tests if needed**

Review tests for:
- Duplicated setup that can be extracted to fixtures
- Tests that are too tightly coupled to implementation details
- Missing edge cases revealed during implementation

---

### Phase 5: Map and validate

**Step 12 -- Map new code files to the component**

For every new file created during implementation:

```bash
pathfinder map <component-id> <file-path>
```

Examples:

```bash
pathfinder map core/orders src/domain/orders/service.py
pathfinder map core/orders src/domain/orders/models.py
pathfinder map core/orders src/domain/orders/validators.py
pathfinder map core/orders tests/test_orders.py
```

**Step 13 -- Verify no unmapped files remain**

```bash
pathfinder unmapped
```

Every file you created should be mapped.

**Step 14 -- Run drift check**

```bash
pathfinder drift check
```

This verifies that the implementation matches the component spec. If drift is detected:

- **Code does more than spec says:** Update the spec to reflect the actual implementation, or remove the extra code
- **Code does less than spec says:** You missed something -- go back to Phase 3 and implement it
- **Contract mismatch:** The implementation's actual inputs/outputs do not match the declared contract -- fix the implementation or update the contract (with user approval)

**Step 15 -- Run full validation**

```bash
pathfinder validate
```

Fix any issues.

---

### Phase 6: Report

**Step 16 -- Summarize the implementation**

Present to the user:

```
== Implementation Complete ==

Component: core/orders
Task: Implement order creation with payment processing

Files created:
  - src/domain/orders/service.py      (mapped to core/orders)
  - src/domain/orders/models.py       (mapped to core/orders)
  - src/domain/orders/validators.py   (mapped to core/orders)
  - tests/test_orders.py              (mapped to core/orders)

Tests: 12 passed, 0 failed
Drift check: clean
Validation: passing

Contract compliance:
  - Input contract: CreateOrderRequest -- implemented and tested
  - Output contract: OrderResponse, ValidationError -- implemented and tested
  - Dependency contracts: core/payments, infra/notifications -- mocked in tests

Notes:
  - [any observations, contract concerns, or follow-up items]
```

---

## Contract violation protocol

If during implementation you discover that a contract cannot be satisfied as specified:

1. **Stop implementing** -- do not work around the contract
2. **Document the issue** -- what specifically cannot work as specified
3. **Present options to the user:**
   - Update the contract to match what is feasible
   - Change the component design to satisfy the original contract
   - Adjust dependent components that set this contract
4. **Wait for the user's decision** before proceeding
5. After the decision, update the contract in pathfinder:

```bash
pathfinder set <component-id> contract.inputs "<updated input contract>"
pathfinder set <component-id> contract.outputs "<updated output contract>"
```

Then resume implementation.

## Multi-component implementation

If the task requires implementing across multiple components:

1. **Implement one component at a time** -- complete the full RED-GREEN-REFACTOR cycle for each
2. **Start with leaf components** (those with no dependencies on other unimplemented components)
3. **Work upward** -- implement components that depend on already-implemented ones
4. **Run cross-component integration tests last** -- after all individual components pass their unit tests

Order of implementation:

```
1. data/orders        (leaf -- no dependencies on other new components)
2. infra/payment-gw   (leaf -- wraps external service)
3. core/orders        (depends on data/orders and infra/payment-gw)
4. api/gateway         (depends on core/orders)
```

## Decision points

| Situation | Decision |
|---|---|
| No contracts defined for the component | Ask the user to define contracts first (use pathfinder-define) or infer from the task description and confirm with user |
| Test requires complex mock setup | Simplify the component's interface; complex mocks signal a design problem |
| Implementation needs a new dependency | Do not add it silently; propose it and update the architecture |
| Tests pass but drift check fails | The spec is out of date -- update it, do not disable drift checking |
| Existing tests break | Your change has wider impact than expected; use pathfinder-check to analyze |

## Output

When this skill completes:

- All new code files are written and mapped to their component
- All tests pass (unit and, if applicable, integration)
- Drift check is clean
- Validation passes
- A summary report is provided to the user
