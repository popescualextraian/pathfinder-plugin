# Model Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the data model with dependsOn, external components, dynamic types, contract versions, flow patterns, and spec/contract CLI before writing integration tests.

**Architecture:** Six incremental changes to types.py, core layer, and CLI. Each task is self-contained — types first, then core, then CLI+tests. No task depends on a later task.

**Tech Stack:** Python 3.12, Click, PyYAML, pytest with CliRunner.

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `pathfinder/types.py` | Add fields to Component, DataFlow, Contract, IndexEntry |
| Modify | `pathfinder/core/graph.py` | Union dependsOn + flow edges in deps/dependents/trace |
| Modify | `pathfinder/core/index_builder.py` | Copy dependsOn/external into index, validate dependsOn targets |
| Modify | `pathfinder/core/storage.py` | Seed componentTypes in init_project, load/save helpers |
| Modify | `pathfinder/cli/add_cmd.py` | --external flag, type validation with prompt |
| Modify | `pathfinder/cli/set_cmd.py` | --spec and --spec-file options |
| Modify | `pathfinder/cli/flows_cmd.py` | --pattern option on flow-add, pattern display |
| Modify | `pathfinder/cli/show_cmd.py` | Show version in contracts, show dependsOn |
| Modify | `pathfinder/cli/deps_cmd.py` | No code change needed (uses graph functions) |
| Modify | `pathfinder/cli/drift_cmd.py` | Skip code-mapping check for external components |
| Modify | `pathfinder/cli/validate_cmd.py` | No code change needed (uses validate_index) |
| Modify | `pathfinder/cli/main.py` | Register depend_cmd, contract_add_cmd, contract_remove_cmd |
| Create | `pathfinder/cli/depend_cmd.py` | depend command (add/remove dependsOn) |
| Create | `pathfinder/cli/contract_cmd.py` | contract-add, contract-remove commands |
| Create | `tests/cli/test_depend.py` | Tests for depend command |
| Create | `tests/cli/test_contract.py` | Tests for contract commands |
| Modify | `tests/core/test_graph.py` | Tests for dependsOn in graph queries |
| Modify | `tests/core/test_index_builder.py` | Tests for dependsOn/external in index |
| Modify | `tests/cli/test_add.py` | Tests for --external flag and type validation |
| Modify | `tests/cli/test_set.py` | Tests for --spec and --spec-file |
| Modify | `tests/cli/test_flows.py` | Tests for --pattern |
| Modify | `tests/cli/test_validate.py` | Tests for dependsOn validation |
| Modify | `tests/cli/test_drift.py` | Tests for external component skip |

---

### Task 1: Add `dependsOn` to types and core

**Files:**
- Modify: `pathfinder/types.py:42-52` (Component), `pathfinder/types.py:73-83` (IndexEntry)
- Modify: `pathfinder/core/index_builder.py:17-62` (build_index), `pathfinder/core/index_builder.py:91-141` (validate_index)
- Modify: `pathfinder/core/graph.py:6-18` (get_dependencies, get_dependents)
- Test: `tests/core/test_graph.py`, `tests/core/test_index_builder.py`

- [ ] **Step 1: Write failing tests for dependsOn in graph**

Add to `tests/core/test_graph.py`:

```python
# Inside the graph_index fixture, update "order" to include dependsOn:
# Change the "order" save_component call to:
save_component(test_dir, {"id": "order", "name": "Order", "type": "service", "status": "active",
    "dataFlows": [{"to": "payment", "data": "PaymentRequest", "protocol": "REST"}],
    "codeMappings": [{"glob": "src/order/**"}],
    "dependsOn": ["notification"]})

# Add new test class after TestGetDependencies:
class TestDependsOn:
    def test_deps_includes_depends_on(self, graph_index):
        deps = get_dependencies(graph_index, "order")
        assert "payment" in deps      # from flow
        assert "notification" in deps  # from dependsOn

    def test_dependents_includes_depends_on(self, graph_index):
        dependents = get_dependents(graph_index, "notification")
        assert "order" in dependents   # from order's dependsOn

    def test_structural_deps_only(self, graph_index):
        from pathfinder.core.graph import get_structural_deps
        deps = get_structural_deps(graph_index, "order")
        assert "notification" in deps
        assert "payment" not in deps   # payment is flow-based, not structural
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_graph.py::TestDependsOn -v`
Expected: FAIL — dependsOn not in index, get_structural_deps not defined

- [ ] **Step 3: Write failing tests for dependsOn in index builder**

Add to `tests/core/test_index_builder.py`:

```python
def test_indexes_depends_on(test_dir):
    save_component(test_dir, {"id": "frontend", "name": "Frontend", "type": "module", "status": "active",
        "dependsOn": ["design-system"]})
    save_component(test_dir, {"id": "design-system", "name": "Design System", "type": "library", "status": "active"})
    index = build_index(test_dir)
    assert "design-system" in index["components"]["frontend"]["dependsOn"]


def test_validates_broken_depends_on(test_dir):
    from pathfinder.core.index_builder import validate_index
    save_component(test_dir, {"id": "orphan", "name": "Orphan", "type": "service", "status": "active",
        "dependsOn": ["ghost"]})
    issues = validate_index(test_dir)
    assert any("ghost" in i["issue"] for i in issues)
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `pytest tests/core/test_index_builder.py::test_indexes_depends_on tests/core/test_index_builder.py::test_validates_broken_depends_on -v`
Expected: FAIL — dependsOn not in index entries

- [ ] **Step 5: Update types.py — add depends_on to Component and IndexEntry**

In `pathfinder/types.py`, add `depends_on` field to `Component`:

```python
@dataclass
class Component:
    id: str
    name: str
    type: str
    status: ComponentStatus
    parent: str | None = None
    spec: str | None = None
    contracts: Contracts | None = None
    data_flows: list[DataFlow] = field(default_factory=list)
    code_mappings: list[CodeMapping] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
```

Add `depends_on` to `IndexEntry`:

```python
@dataclass
class IndexEntry:
    id: str
    name: str
    type: str
    status: ComponentStatus
    parent: str | None
    children: list[str]
    tags: list[str]
    data_flows: list[DataFlow]
    code_mappings: list[CodeMapping]
    file_path: str
    depends_on: list[str] = field(default_factory=list)
```

Note: `Component.type` also changes from `ComponentType` to `str` here (Task 3), but do that in Task 3. For now just add the field.

- [ ] **Step 6: Update index_builder.py — copy dependsOn into index**

In `pathfinder/core/index_builder.py`, in `build_index`, add to the entry dict (after `"codeMappings"` line):

```python
"dependsOn": comp.get("dependsOn", []),
```

In `validate_index`, add after the data flow validation block (after line ~118):

```python
        for dep_id in comp.get("dependsOn", []):
            if dep_id not in index["components"]:
                issues.append({
                    "component_id": comp["id"],
                    "issue": f"dependsOn references unknown component '{dep_id}'",
                    "severity": "error",
                })
```

- [ ] **Step 7: Update graph.py — union dependsOn into deps/dependents, add get_structural_deps**

Replace `get_dependencies` and `get_dependents` in `pathfinder/core/graph.py`:

```python
def get_dependencies(index: dict, component_id: str) -> list[str]:
    deps = set()
    for flow in index["flows"]:
        if flow.get("from") == component_id and flow.get("to"):
            deps.add(flow["to"])
    comp = index["components"].get(component_id, {})
    for dep_id in comp.get("dependsOn", []):
        deps.add(dep_id)
    return list(deps)

def get_dependents(index: dict, component_id: str) -> list[str]:
    dependents = set()
    for flow in index["flows"]:
        if flow.get("to") == component_id and flow.get("from"):
            dependents.add(flow["from"])
    for comp in index["components"].values():
        if component_id in comp.get("dependsOn", []):
            dependents.add(comp["id"])
    return list(dependents)

def get_structural_deps(index: dict, component_id: str) -> list[str]:
    comp = index["components"].get(component_id, {})
    return list(comp.get("dependsOn", []))
```

Also update `trace_flow` to walk dependsOn edges too — add after the flow adjacency loop:

```python
    for comp in index["components"].values():
        for dep_id in comp.get("dependsOn", []):
            if dep_id in index["components"]:
                adj.setdefault(comp["id"], set()).add(dep_id)
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/core/test_graph.py tests/core/test_index_builder.py -v`
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add pathfinder/types.py pathfinder/core/graph.py pathfinder/core/index_builder.py tests/core/test_graph.py tests/core/test_index_builder.py
git commit -m "feat: add dependsOn structural dependencies to data model and core"
```

---

### Task 2: `depend` CLI command

**Files:**
- Create: `pathfinder/cli/depend_cmd.py`
- Modify: `pathfinder/cli/main.py:1-51`
- Create: `tests/cli/test_depend.py`

- [ ] **Step 1: Write failing tests**

Create `tests/cli/test_depend.py`:

```python
import tempfile, shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component, load_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "frontend", "name": "Frontend", "type": "module", "status": "active"})
    save_component(d, {"id": "design-system", "name": "Design System", "type": "library", "status": "active"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_adds_dependency(runner, test_dir):
    result = runner.invoke(cli, ["depend", "frontend", "design-system", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "frontend")
    assert "design-system" in comp.get("dependsOn", [])


def test_removes_dependency(runner, test_dir):
    save_component(test_dir, {"id": "frontend", "name": "Frontend", "type": "module", "status": "active",
        "dependsOn": ["design-system"]})
    result = runner.invoke(cli, ["depend", "frontend", "design-system", "--remove", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "frontend")
    assert "design-system" not in comp.get("dependsOn", [])


def test_rejects_unknown_target(runner, test_dir):
    result = runner.invoke(cli, ["depend", "frontend", "ghost", "--root", str(test_dir)])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "Error" in result.output


def test_no_duplicate_dependency(runner, test_dir):
    runner.invoke(cli, ["depend", "frontend", "design-system", "--root", str(test_dir)])
    runner.invoke(cli, ["depend", "frontend", "design-system", "--root", str(test_dir)])
    comp = load_component(test_dir, "frontend")
    assert comp.get("dependsOn", []).count("design-system") == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_depend.py -v`
Expected: FAIL — depend command not registered

- [ ] **Step 3: Create depend_cmd.py**

Create `pathfinder/cli/depend_cmd.py`:

```python
"""Depend command — manage structural dependencies."""

import click

from pathfinder.core.storage import load_component, save_component
from pathfinder.core.index_builder import build_index, ensure_index
from pathfinder.cli.utils import resolve_root


@click.command("depend")
@click.argument("id_")
@click.argument("target")
@click.option("--remove", is_flag=True, help="Remove the dependency")
@click.option("--root", default=None, help="Project root directory")
def depend_cmd(id_: str, target: str, remove: bool, root: str | None):
    """Add or remove a structural dependency."""
    project_root = resolve_root(root)
    component = load_component(project_root, id_)

    if not remove:
        # Verify target exists
        try:
            load_component(project_root, target)
        except FileNotFoundError:
            raise click.ClickException(f"Target component '{target}' not found")

    deps = component.get("dependsOn", [])

    if remove:
        if target in deps:
            deps.remove(target)
            component["dependsOn"] = deps
            save_component(project_root, component)
            build_index(project_root)
            click.echo(f"Removed dependency: {id_} -/-> {target}")
        else:
            click.echo(f"{id_} does not depend on {target}")
    else:
        if target not in deps:
            deps.append(target)
            component["dependsOn"] = deps
            save_component(project_root, component)
            build_index(project_root)
        click.echo(f"Added dependency: {id_} --> {target}")
```

- [ ] **Step 4: Register in main.py**

Add import and registration in `pathfinder/cli/main.py`:

```python
from pathfinder.cli.depend_cmd import depend_cmd
# ...
cli.add_command(depend_cmd)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/cli/test_depend.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add pathfinder/cli/depend_cmd.py pathfinder/cli/main.py tests/cli/test_depend.py
git commit -m "feat: CLI depend command for structural dependencies"
```

---

### Task 3: External components

**Files:**
- Modify: `pathfinder/types.py:42-52` (Component), `pathfinder/types.py:73-83` (IndexEntry)
- Modify: `pathfinder/core/index_builder.py:17-62` (build_index)
- Modify: `pathfinder/cli/add_cmd.py:11-28`
- Modify: `pathfinder/cli/drift_cmd.py:27-45`
- Test: `tests/cli/test_add.py`, `tests/cli/test_drift.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/cli/test_add.py`:

```python
def test_adds_external_component(runner, test_dir):
    result = runner.invoke(cli, ["add", "service", "Stripe API", "--external", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "stripe-api")
    assert comp.get("external") is True
```

Add to `tests/cli/test_drift.py`:

```python
def test_skips_code_mapping_check_for_external(runner, test_dir):
    save_component(test_dir, {"id": "ext-stripe", "name": "Stripe", "type": "service",
        "status": "active", "external": True})
    result = runner.invoke(cli, ["drift", "check", "--root", str(test_dir)])
    # External components should not trigger "no code mappings" warning
    assert "ext-stripe" not in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_add.py::test_adds_external_component tests/cli/test_drift.py::test_skips_code_mapping_check_for_external -v`
Expected: FAIL — --external flag doesn't exist, drift doesn't skip externals

- [ ] **Step 3: Update types.py — add external field**

Add to `Component` dataclass (after `tags`):

```python
    external: bool = False
```

Add to `IndexEntry` dataclass (after `depends_on`):

```python
    external: bool = False
```

- [ ] **Step 4: Update index_builder.py — copy external into index**

In `build_index`, add to the entry dict:

```python
"external": comp.get("external", False),
```

- [ ] **Step 5: Update add_cmd.py — --external flag**

In `pathfinder/cli/add_cmd.py`, add the option and pass it through:

```python
@click.command("add")
@click.argument("type_", metavar="TYPE")
@click.argument("name")
@click.option("--parent", default=None, help="Parent component ID")
@click.option("--external", is_flag=True, help="Mark as external component")
@click.option("--root", default=None, help="Project root directory")
def add_cmd(type_: str, name: str, parent: str | None, external: bool, root: str | None):
    """Add a new component."""
    project_root = resolve_root(root)
    slug = name_to_slug(name)
    comp_id = f"{parent}.{slug}" if parent else slug
    if parent:
        try:
            load_component(project_root, parent)
        except FileNotFoundError:
            raise click.ClickException(f"Parent component '{parent}' not found")
    comp = {"id": comp_id, "name": name, "type": type_, "status": "active", "parent": parent}
    if external:
        comp["external"] = True
    save_component(project_root, comp)
    build_index(project_root)
    click.echo(f"Added {type_} '{name}' ({comp_id})")
```

- [ ] **Step 6: Update drift_cmd.py — skip externals in code-mapping checks**

In `pathfinder/cli/drift_cmd.py`, update the unmapped leaf check (around line 39):

```python
    # Check for unmapped leaf components (skip externals)
    for comp in index["components"].values():
        if comp.get("external"):
            continue
        if not comp.get("codeMappings") and comp.get("children") == []:
            issues.append({
                "component_id": comp["id"],
                "issue": "Leaf component has no code mappings",
                "severity": "warning",
            })
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/cli/test_add.py tests/cli/test_drift.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add pathfinder/types.py pathfinder/core/index_builder.py pathfinder/cli/add_cmd.py pathfinder/cli/drift_cmd.py tests/cli/test_add.py tests/cli/test_drift.py
git commit -m "feat: external components with --external flag and drift skip"
```

---

### Task 4: Dynamic component types

**Files:**
- Modify: `pathfinder/types.py:9` (remove ComponentType Literal)
- Modify: `pathfinder/core/storage.py:39-45` (seed componentTypes in init)
- Modify: `pathfinder/cli/add_cmd.py` (type validation)
- Test: `tests/cli/test_add.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/cli/test_add.py`:

```python
def test_accepts_predefined_type(runner, test_dir):
    result = runner.invoke(cli, ["add", "infrastructure", "Redis", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert "Added" in result.output


def test_prompts_for_unknown_type(runner, test_dir):
    result = runner.invoke(cli, ["add", "gateway", "API Gateway", "--root", str(test_dir)], input="y\n")
    assert result.exit_code == 0
    assert "Added" in result.output
    # Verify type was added to config
    from pathfinder.core.storage import load_config
    config = load_config(test_dir)
    assert "gateway" in config.get("componentTypes", [])


def test_rejects_unknown_type_when_declined(runner, test_dir):
    result = runner.invoke(cli, ["add", "gateway", "API Gateway", "--root", str(test_dir)], input="n\n")
    assert result.exit_code != 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_add.py::test_accepts_predefined_type tests/cli/test_add.py::test_prompts_for_unknown_type tests/cli/test_add.py::test_rejects_unknown_type_when_declined -v`
Expected: FAIL — no type validation or prompt

- [ ] **Step 3: Remove ComponentType Literal from types.py**

In `pathfinder/types.py`, remove:

```python
ComponentType = Literal["system", "module", "service", "component", "sub-component"]
```

Change `Component.type` and `IndexEntry.type` from `ComponentType` to `str`. Remove the unused `Literal` import if no other Literal remains (ComponentStatus still uses it, so keep the import).

- [ ] **Step 4: Update storage.py — seed componentTypes in init_project**

In `pathfinder/core/storage.py`, update `init_project`:

```python
DEFAULT_COMPONENT_TYPES = [
    "system", "module", "service", "component", "sub-component",
    "library", "infrastructure", "pipeline", "database",
]


def init_project(project_root: Path, name: str) -> None:
    project_root = Path(project_root)
    _assert_not_initialized(project_root)
    pf_dir = get_pathfinder_dir(project_root)
    pf_dir.mkdir(parents=True, exist_ok=True)
    (pf_dir / "components").mkdir(exist_ok=True)
    save_config(project_root, {"name": name, "componentTypes": list(DEFAULT_COMPONENT_TYPES)})
```

- [ ] **Step 5: Update add_cmd.py — validate type against config list**

Replace `pathfinder/cli/add_cmd.py`:

```python
"""Add command."""
import re
import click
from pathfinder.core.storage import save_component, load_component, load_config, save_config
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


def name_to_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@click.command("add")
@click.argument("type_", metavar="TYPE")
@click.argument("name")
@click.option("--parent", default=None, help="Parent component ID")
@click.option("--external", is_flag=True, help="Mark as external component")
@click.option("--root", default=None, help="Project root directory")
def add_cmd(type_: str, name: str, parent: str | None, external: bool, root: str | None):
    """Add a new component."""
    project_root = resolve_root(root)

    config = load_config(project_root)
    known_types = config.get("componentTypes", [])
    if known_types and type_ not in known_types:
        if not click.confirm(f"Type '{type_}' is not in known types. Add it?"):
            raise click.ClickException(f"Aborted. Known types: {', '.join(known_types)}")
        known_types.append(type_)
        config["componentTypes"] = known_types
        save_config(project_root, config)

    slug = name_to_slug(name)
    comp_id = f"{parent}.{slug}" if parent else slug
    if parent:
        try:
            load_component(project_root, parent)
        except FileNotFoundError:
            raise click.ClickException(f"Parent component '{parent}' not found")
    comp = {"id": comp_id, "name": name, "type": type_, "status": "active", "parent": parent}
    if external:
        comp["external"] = True
    save_component(project_root, comp)
    build_index(project_root)
    click.echo(f"Added {type_} '{name}' ({comp_id})")
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/cli/test_add.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add pathfinder/types.py pathfinder/core/storage.py pathfinder/cli/add_cmd.py tests/cli/test_add.py
git commit -m "feat: dynamic component types with predefined list and prompt"
```

---

### Task 5: Contract version field

**Files:**
- Modify: `pathfinder/types.py:14-18` (Contract dataclass)
- Modify: `pathfinder/cli/show_cmd.py:7-47` (display version)
- Test: `tests/cli/test_show.py`

- [ ] **Step 1: Write failing test**

Add to `tests/cli/test_show.py` (read the file first to find existing fixture pattern):

```python
def test_shows_contract_version(runner, test_dir):
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "service", "status": "active",
        "contracts": {"outputs": [{"name": "OrderCreated", "format": "{orderId, total}", "version": "2.0"}]}})
    result = runner.invoke(cli, ["show", "payment", "--contracts", "--root", str(test_dir)])
    assert "2.0" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_show.py::test_shows_contract_version -v`
Expected: FAIL — version not displayed

- [ ] **Step 3: Update types.py — add version to Contract**

```python
@dataclass
class Contract:
    name: str
    format: str
    source: str | None = None
    target: str | None = None
    version: str | None = None
```

- [ ] **Step 4: Update show_cmd.py — display version**

In `pathfinder/cli/show_cmd.py`, update the contracts display sections. In the `--contracts` branch, after source/target lines:

```python
        for inp in c.get("inputs", []):
            source = f" (from: {inp['source']})" if inp.get("source") else ""
            version = f" v{inp['version']}" if inp.get("version") else ""
            click.echo(f"\n  Input: {inp['name']}{source}{version}")
            click.echo(f"    {inp['format'].strip()}")
        for out in c.get("outputs", []):
            target = f" (to: {out['target']})" if out.get("target") else ""
            version = f" v{out['version']}" if out.get("version") else ""
            click.echo(f"\n  Output: {out['name']}{target}{version}")
            click.echo(f"    {out['format'].strip()}")
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/cli/test_show.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add pathfinder/types.py pathfinder/cli/show_cmd.py tests/cli/test_show.py
git commit -m "feat: contract version field with display in show --contracts"
```

---

### Task 6: Flow pattern field

**Files:**
- Modify: `pathfinder/types.py:28-33` (DataFlow dataclass)
- Modify: `pathfinder/cli/flows_cmd.py:51-69` (flow-add --pattern, display)
- Modify: `pathfinder/core/index_builder.py:42-50` (copy pattern into index flows)
- Test: `tests/cli/test_flows.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/cli/test_flows.py`:

```python
def test_flow_add_with_pattern(runner, test_dir):
    result = runner.invoke(cli, ["flow-add", "payment", "ledger", "--data", "Event", "--protocol", "kafka", "--pattern", "publish", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    flow = next(f for f in comp.get("dataFlows", []) if f["data"] == "Event")
    assert flow["pattern"] == "publish"


def test_flows_displays_pattern(runner, test_dir):
    save_component(test_dir, {"id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "OrderEvent", "protocol": "kafka", "pattern": "publish"}]})
    result = runner.invoke(cli, ["flows", "--root", str(test_dir)])
    assert "kafka/publish" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_flows.py::test_flow_add_with_pattern tests/cli/test_flows.py::test_flows_displays_pattern -v`
Expected: FAIL — --pattern not accepted, pattern not displayed

- [ ] **Step 3: Update types.py — add pattern to DataFlow**

```python
@dataclass
class DataFlow:
    data: str
    from_id: str | None = None
    to: str | None = None
    protocol: str | None = None
    pattern: str | None = None
```

- [ ] **Step 4: Update index_builder.py — copy pattern into flows**

In `build_index`, update the flow collection loop:

```python
    flows: list[dict] = []
    for comp in components:
        for flow in comp.get("dataFlows", []):
            entry = {
                "from": flow.get("from", comp["id"]),
                "to": flow.get("to"),
                "data": flow["data"],
                "protocol": flow.get("protocol"),
                "pattern": flow.get("pattern"),
            }
            flows.append(entry)
```

- [ ] **Step 5: Update flows_cmd.py — --pattern option and display**

In `flows_cmd`, update display to show pattern:

```python
    for flow in flows:
        protocol = flow.get("protocol", "")
        pattern = flow.get("pattern", "")
        if protocol and pattern:
            suffix = f" [{protocol}/{pattern}]"
        elif protocol:
            suffix = f" [{protocol}]"
        elif pattern:
            suffix = f" [{pattern}]"
        else:
            suffix = ""
        click.echo(f"  {flow['from']} → {flow['to']}: {flow['data']}{suffix}")
```

In `flow_add_cmd`, add `--pattern` option:

```python
@click.command("flow-add")
@click.argument("from_id")
@click.argument("to_id")
@click.option("--data", required=True, help="Description of data that flows")
@click.option("--protocol", default=None, help="Protocol (e.g., REST, kafka)")
@click.option("--pattern", default=None, help="Pattern (e.g., publish, subscribe)")
@click.option("--root", default=None, help="Project root directory")
def flow_add_cmd(from_id, to_id, data, protocol, pattern, root):
    """Add a data flow between components."""
    project_root = resolve_root(root)
    component = load_component(project_root, from_id)
    flows = component.get("dataFlows", [])
    new_flow = {"to": to_id, "data": data}
    if protocol:
        new_flow["protocol"] = protocol
    if pattern:
        new_flow["pattern"] = pattern
    flows.append(new_flow)
    component["dataFlows"] = flows
    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Added flow: {from_id} → {to_id} ({data})")
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/cli/test_flows.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add pathfinder/types.py pathfinder/core/index_builder.py pathfinder/cli/flows_cmd.py tests/cli/test_flows.py
git commit -m "feat: flow pattern field for publish/subscribe semantics"
```

---

### Task 7: Spec and contract CLI commands

**Files:**
- Modify: `pathfinder/cli/set_cmd.py:10-51`
- Create: `pathfinder/cli/contract_cmd.py`
- Modify: `pathfinder/cli/main.py`
- Modify: `tests/cli/test_set.py`
- Create: `tests/cli/test_contract.py`

- [ ] **Step 1: Write failing tests for --spec on set command**

Add to `tests/cli/test_set.py`:

```python
def test_sets_spec_inline(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--spec", "Handles all payment processing", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert comp["spec"] == "Handles all payment processing"


def test_sets_spec_from_file(runner, test_dir, tmp_path):
    spec_file = tmp_path / "spec.md"
    spec_file.write_text("# Payment\nHandles payments via Stripe.")
    runner.invoke(cli, ["set", "payment", "--spec-file", str(spec_file), "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert "Stripe" in comp["spec"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_set.py::test_sets_spec_inline tests/cli/test_set.py::test_sets_spec_from_file -v`
Expected: FAIL — --spec and --spec-file not accepted

- [ ] **Step 3: Update set_cmd.py — add --spec and --spec-file**

In `pathfinder/cli/set_cmd.py`:

```python
@click.command("set")
@click.argument("id_")
@click.option("--status", default=None, help="Set status (proposed, active, deprecated)")
@click.option("--type", "type_", default=None, help="Set type")
@click.option("--tag", default=None, help="Add a tag")
@click.option("--remove-tag", default=None, help="Remove a tag")
@click.option("--spec", default=None, help="Set spec text")
@click.option("--spec-file", default=None, type=click.Path(exists=True), help="Set spec from file")
@click.option("--root", default=None, help="Project root directory")
def set_cmd(id_: str, status, type_, tag, remove_tag, spec, spec_file, root):
    """Update component fields."""
    project_root = resolve_root(root)
    component = load_component(project_root, id_)
    changes = []

    if status:
        component["status"] = status
        changes.append(f"status → {status}")

    if type_:
        component["type"] = type_
        changes.append(f"type → {type_}")

    if tag:
        tags = component.get("tags", [])
        if tag not in tags:
            tags.append(tag)
            component["tags"] = tags
            changes.append(f"+tag {tag}")

    if remove_tag:
        tags = component.get("tags", [])
        if remove_tag in tags:
            tags.remove(remove_tag)
            component["tags"] = tags
            changes.append(f"-tag {remove_tag}")

    if spec:
        component["spec"] = spec
        changes.append("spec updated")

    if spec_file:
        component["spec"] = Path(spec_file).read_text()
        changes.append(f"spec loaded from {spec_file}")

    if not changes:
        click.echo("No changes specified")
        return

    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Updated {component['name']} ({id_}): {', '.join(changes)}")
```

Add `from pathlib import Path` at the top of set_cmd.py.

- [ ] **Step 4: Run set tests**

Run: `pytest tests/cli/test_set.py -v`
Expected: ALL PASS

- [ ] **Step 5: Write failing tests for contract commands**

Create `tests/cli/test_contract.py`:

```python
import tempfile, shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component, load_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "payment", "name": "Payment", "type": "service", "status": "active"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_adds_input_contract(runner, test_dir):
    result = runner.invoke(cli, ["contract-add", "payment", "--input",
        "--name", "PaymentRequest", "--format", "POST /pay {amount}", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    inputs = comp.get("contracts", {}).get("inputs", [])
    assert any(c["name"] == "PaymentRequest" for c in inputs)


def test_adds_output_contract(runner, test_dir):
    result = runner.invoke(cli, ["contract-add", "payment", "--output",
        "--name", "PaymentResult", "--format", "{status, txId}", "--version", "2.0", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    outputs = comp.get("contracts", {}).get("outputs", [])
    out = next(c for c in outputs if c["name"] == "PaymentResult")
    assert out["version"] == "2.0"


def test_adds_contract_with_source(runner, test_dir):
    result = runner.invoke(cli, ["contract-add", "payment", "--input",
        "--name", "OrderData", "--format", "{orderId}", "--source", "order-service", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    inp = comp["contracts"]["inputs"][0]
    assert inp["source"] == "order-service"


def test_removes_contract(runner, test_dir):
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "service", "status": "active",
        "contracts": {"inputs": [{"name": "PaymentRequest", "format": "POST /pay"}], "outputs": []}})
    result = runner.invoke(cli, ["contract-remove", "payment", "--name", "PaymentRequest", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    inputs = comp.get("contracts", {}).get("inputs", [])
    assert not any(c["name"] == "PaymentRequest" for c in inputs)


def test_requires_input_or_output_flag(runner, test_dir):
    result = runner.invoke(cli, ["contract-add", "payment",
        "--name", "X", "--format", "Y", "--root", str(test_dir)])
    assert result.exit_code != 0
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `pytest tests/cli/test_contract.py -v`
Expected: FAIL — contract-add and contract-remove not registered

- [ ] **Step 7: Create contract_cmd.py**

Create `pathfinder/cli/contract_cmd.py`:

```python
"""Contract commands — contract-add, contract-remove."""

import click

from pathfinder.core.storage import load_component, save_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("contract-add")
@click.argument("id_")
@click.option("--input", "is_input", is_flag=True, help="Add as input contract")
@click.option("--output", "is_output", is_flag=True, help="Add as output contract")
@click.option("--name", required=True, help="Contract name")
@click.option("--format", "fmt", required=True, help="Contract format description")
@click.option("--version", default=None, help="Contract version")
@click.option("--source", default=None, help="Source component (for inputs)")
@click.option("--target", default=None, help="Target component (for outputs)")
@click.option("--root", default=None, help="Project root directory")
def contract_add_cmd(id_: str, is_input: bool, is_output: bool, name: str, fmt: str,
                     version: str | None, source: str | None, target: str | None, root: str | None):
    """Add a contract to a component."""
    if not is_input and not is_output:
        raise click.ClickException("Specify --input or --output")

    project_root = resolve_root(root)
    component = load_component(project_root, id_)
    contracts = component.get("contracts", {"inputs": [], "outputs": []})
    if "inputs" not in contracts:
        contracts["inputs"] = []
    if "outputs" not in contracts:
        contracts["outputs"] = []

    contract = {"name": name, "format": fmt}
    if version:
        contract["version"] = version

    if is_input:
        if source:
            contract["source"] = source
        contracts["inputs"].append(contract)
        direction = "input"
    else:
        if target:
            contract["target"] = target
        contracts["outputs"].append(contract)
        direction = "output"

    component["contracts"] = contracts
    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Added {direction} contract '{name}' to {component['name']} ({id_})")


@click.command("contract-remove")
@click.argument("id_")
@click.option("--name", required=True, help="Contract name to remove")
@click.option("--root", default=None, help="Project root directory")
def contract_remove_cmd(id_: str, name: str, root: str | None):
    """Remove a contract from a component."""
    project_root = resolve_root(root)
    component = load_component(project_root, id_)
    contracts = component.get("contracts", {"inputs": [], "outputs": []})

    found = False
    for direction in ("inputs", "outputs"):
        original = contracts.get(direction, [])
        filtered = [c for c in original if c["name"] != name]
        if len(filtered) < len(original):
            found = True
            contracts[direction] = filtered

    if not found:
        raise click.ClickException(f"Contract '{name}' not found on {id_}")

    component["contracts"] = contracts
    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Removed contract '{name}' from {component['name']} ({id_})")
```

- [ ] **Step 8: Register in main.py**

Add imports and commands:

```python
from pathfinder.cli.contract_cmd import contract_add_cmd, contract_remove_cmd
# ...
cli.add_command(contract_add_cmd)
cli.add_command(contract_remove_cmd)
```

- [ ] **Step 9: Run all tests**

Run: `pytest tests/cli/test_contract.py tests/cli/test_set.py -v`
Expected: ALL PASS

- [ ] **Step 10: Commit**

```bash
git add pathfinder/cli/set_cmd.py pathfinder/cli/contract_cmd.py pathfinder/cli/main.py tests/cli/test_set.py tests/cli/test_contract.py
git commit -m "feat: spec/contract CLI — set --spec, contract-add, contract-remove"
```

---

### Task 8: Show dependsOn and external in display commands

**Files:**
- Modify: `pathfinder/cli/show_cmd.py:7-47`
- Modify: `pathfinder/cli/search_cmd.py:9-43`
- Test: `tests/cli/test_show.py`, `tests/cli/test_search.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/cli/test_show.py`:

```python
def test_shows_depends_on(runner, test_dir):
    save_component(test_dir, {"id": "lib", "name": "Lib", "type": "library", "status": "active"})
    save_component(test_dir, {"id": "app", "name": "App", "type": "module", "status": "active",
        "dependsOn": ["lib"]})
    result = runner.invoke(cli, ["show", "app", "--root", str(test_dir)])
    assert "lib" in result.output
    assert "Depends on" in result.output


def test_shows_external_marker(runner, test_dir):
    save_component(test_dir, {"id": "stripe", "name": "Stripe", "type": "service", "status": "active",
        "external": True})
    result = runner.invoke(cli, ["show", "stripe", "--root", str(test_dir)])
    assert "external" in result.output.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_show.py::test_shows_depends_on tests/cli/test_show.py::test_shows_external_marker -v`
Expected: FAIL — dependsOn and external not displayed

- [ ] **Step 3: Update show_cmd.py**

In the non-contracts branch of `show_cmd`, after the parent line add:

```python
    if component.get("external"):
        click.echo("External: yes")
    if component.get("dependsOn"):
        click.echo(f"Depends on: {', '.join(component['dependsOn'])}")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/cli/test_show.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add pathfinder/cli/show_cmd.py tests/cli/test_show.py
git commit -m "feat: show dependsOn and external marker in display"
```

---

### Task 9: Validate dependsOn targets

**Files:**
- Modify: `tests/cli/test_validate.py`

- [ ] **Step 1: Write failing test**

Add to `tests/cli/test_validate.py`:

```python
def test_reports_broken_depends_on_target(runner, test_dir):
    save_component(test_dir, {"id": "app", "name": "App", "type": "module", "status": "active",
        "dependsOn": ["ghost"]})
    result = runner.invoke(cli, ["validate", "--root", str(test_dir)])
    assert "ghost" in result.output
```

- [ ] **Step 2: Run test**

Run: `pytest tests/cli/test_validate.py::test_reports_broken_depends_on_target -v`
Expected: PASS (already implemented in Task 1's validate_index change)

If it passes, no code changes needed. If it fails, the Task 1 validate_index change was missed — go add it.

- [ ] **Step 3: Commit test**

```bash
git add tests/cli/test_validate.py
git commit -m "test: validate dependsOn targets in CLI"
```

---

### Task 10: Full regression

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: ALL PASS

- [ ] **Step 2: Fix any regressions**

If any existing tests broke (e.g., init tests that check config shape, or tests that rely on ComponentType Literal), fix them. Likely candidates:
- Tests that create components with `init_project` — config now includes `componentTypes`
- Tests that check exact config content

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: regression fixes from model hardening"
```
