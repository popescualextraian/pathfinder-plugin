# Model Hardening — Pre-Integration-Test Changes

Six changes to the data model and CLI identified by stress-testing against realistic scenarios (UI app, microservices, ML pipeline).

## 1. `dependsOn` — Structural Dependencies

Build-time, library, and infrastructure dependencies that aren't data flows.

**Component YAML:**
```yaml
dependsOn:
  - design-system.forms
  - design-system.buttons
```

**Types:** `depends_on: list[str]` on `Component` and `IndexEntry`.

**Graph:**
- `get_dependencies()` unions flow targets + dependsOn
- `get_dependents()` reverse lookup across both
- `trace()` walks both edge types
- New `get_structural_deps()` / `get_structural_dependents()` for dependsOn-only

**CLI:** `pathfinder depend <id> <target>` adds, `--remove` flag removes.

**Validation:** `validate_index` checks dependsOn targets exist.

**Index builder:** Copies `dependsOn` into index entries. Adds dependency edges to a new `dependencies` list in the index (parallel to `flows`).

## 2. External Components

A component with `external: true`. No new concept — same hierarchy, same graph. Represents boundaries you depend on but don't own.

```yaml
id: ext.stripe
name: Stripe API
type: service
status: active
external: true
contracts:
  inputs:
    - name: Payment Intent
      format: "POST /v1/payment_intents {amount, currency}"
      version: "2024-01"
```

**Types:** `external: bool = False` on `Component` and `IndexEntry`.

**CLI:** `pathfinder add service "Stripe API" --external`.

**Behavior:** Drift check skips code-mapping checks for externals. Validate treats missing mappings on externals as fine.

## 3. Dynamic Component Types

Replace `ComponentType` Literal with a convention-backed string.

**Predefined types** in `.pathfinder/config.yaml`:
```yaml
componentTypes:
  - system
  - module
  - service
  - component
  - sub-component
  - library
  - infrastructure
  - pipeline
  - database
```

**`types.py`:** Remove `ComponentType` Literal. `Component.type` becomes `str`.

**CLI `add`:** If type not in list, prompt to confirm and add. Non-interactive mode (CI) accepts any type.

**Validation:** `drift check` warns on unknown types (not error).

**Init:** `init_project` seeds config with the predefined list.

## 4. Contract Version

`version: str | None = None` on `Contract` dataclass.

```yaml
contracts:
  outputs:
    - name: OrderCreated
      format: "{orderId, items[], total, currency}"
      version: "2.0"
```

Shown in `pathfinder show --contracts` output.

## 5. Spec and Contract CLI Commands

**Spec:** `pathfinder set <id> --spec "text"` and `--spec-file <path>`.

**Contracts:**
```bash
pathfinder contract-add <id> --input --name "X" --format "..." [--version "1.0"] [--source <id>]
pathfinder contract-add <id> --output --name "X" --format "..." [--version "1.0"] [--target <id>]
pathfinder contract-remove <id> --name "X"
```

## 6. Flow Pattern Field

`pattern: str | None = None` on `DataFlow`. Captures publish/subscribe/fire-and-forget semantics.

```yaml
dataFlows:
  - to: event-bus
    data: OrderCreated
    protocol: kafka
    pattern: publish
```

**CLI:** `pathfinder flow-add <from> <to> --data X --pattern publish`

**Display:** `order-service → event-bus: OrderCreated [kafka/publish]`

## Implementation Order

1 → 2 → 3 → 4 → 6 → 5

Each step: update types → update core → update CLI → update tests.
