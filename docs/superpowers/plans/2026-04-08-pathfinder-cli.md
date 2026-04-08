# Pathfinder CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `pathfinder` CLI tool that manages a hierarchical component graph with data flows, code mappings, and drift detection.

**Architecture:** Python CLI using click for command parsing, PyYAML for YAML storage, and an in-memory adjacency list graph rebuilt from a generated JSON index. The `.pathfinder/` directory is the project root for all component data. Skills and agents are markdown files distributed alongside the CLI.

**Tech Stack:** Python 3.12+, click, PyYAML, pytest, pathlib, fnmatch

---

## File Structure

```
pathfinder/
  pathfinder/                     # Python package
    __init__.py
    types.py                      # All shared types (dataclasses)
    cli/
      __init__.py
      main.py                     # click group, registers all commands
      init_cmd.py                 # init command
      add_cmd.py                  # add command
      set_cmd.py                  # set command (update fields)
      remove_cmd.py               # remove command (recursive with warnings)
      move_cmd.py                 # move command
      list_cmd.py                 # list command (tree view)
      info_cmd.py                 # info command (project summary)
      show_cmd.py                 # show + children commands
      search_cmd.py               # search command (by name, tag, type)
      deps_cmd.py                 # deps + dependents commands
      flows_cmd.py                # flows + flow-add + trace commands
      map_cmd.py                  # map + unmapped + mapped commands
      drift_cmd.py                # drift check command (with --ci flag)
      validate_cmd.py             # validate command (structural integrity)
      standards_cmd.py            # standards command
      export_cmd.py               # export command (json, dot, markdown)
      utils.py                    # shared CLI utilities
    core/
      __init__.py
      storage.py                  # Read/write YAML files, manage .pathfinder/ directory
      index_builder.py            # Build index.json from YAML component files
      graph.py                    # Graph operations: deps, dependents, trace, flow queries
  tests/
    __init__.py
    core/
      __init__.py
      test_storage.py
      test_index_builder.py
      test_graph.py
    cli/
      __init__.py
      test_init.py
      test_add.py
      test_set.py
      test_remove.py
      test_move.py
      test_list.py
      test_info.py
      test_show.py
      test_search.py
      test_deps.py
      test_flows.py
      test_map.py
      test_drift.py
      test_validate.py
      test_standards.py
      test_export.py
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
    system-architect.md
  pyproject.toml
```

---

### Task 1: Project Scaffolding + Types

**Files:**
- Create: `pyproject.toml`
- Create: `pathfinder/__init__.py`
- Create: `pathfinder/types.py`
- Create: `pathfinder/cli/__init__.py`
- Create: `pathfinder/cli/main.py`
- Create: `pathfinder/core/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/core/__init__.py`
- Create: `tests/cli/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pathfinder"
version = "0.1.0"
description = "Architecture-first component library CLI"
requires-python = ">=3.12"
dependencies = [
    "click>=8.1",
    "pyyaml>=6.0",
]

[project.scripts]
pathfinder = "pathfinder.cli.main:cli"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-tmp-files>=0.0.2",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create pathfinder/types.py with all shared types**

```python
"""Shared types for Pathfinder."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


ComponentType = Literal["system", "module", "service", "component", "sub-component"]
ComponentStatus = Literal["proposed", "active", "deprecated"]


@dataclass
class Contract:
    name: str
    format: str  # free-form: OpenAPI, TS interface, bullet points, etc.
    source: str | None = None  # component ID (for inputs)
    target: str | None = None  # component ID (for outputs)


@dataclass
class Contracts:
    inputs: list[Contract] = field(default_factory=list)
    outputs: list[Contract] = field(default_factory=list)


@dataclass
class DataFlow:
    data: str  # description of what flows
    from_id: str | None = None  # component ID (serialized as 'from' in YAML)
    to: str | None = None  # component ID
    protocol: str | None = None  # e.g., "REST", "async/event", "sync/internal"


@dataclass
class CodeMapping:
    glob: str  # glob pattern for files
    repo: str | None = None  # repo name from config (optional if single-repo)


@dataclass
class Component:
    id: str
    name: str
    type: ComponentType
    status: ComponentStatus
    parent: str | None = None
    spec: str | None = None
    contracts: Contracts | None = None
    data_flows: list[DataFlow] = field(default_factory=list)
    code_mappings: list[CodeMapping] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class RepoConfig:
    path: str


@dataclass
class ProjectConfig:
    name: str
    repos: dict[str, RepoConfig] = field(default_factory=dict)
    integrations: dict[str, dict] = field(default_factory=dict)


@dataclass
class Standards:
    spec: str


@dataclass
class IndexEntry:
    id: str
    name: str
    type: ComponentType
    status: ComponentStatus
    parent: str | None
    children: list[str]
    tags: list[str]
    data_flows: list[DataFlow]
    code_mappings: list[CodeMapping]
    file_path: str  # path to the YAML file


@dataclass
class ComponentIndex:
    version: int
    generated_at: str
    components: dict[str, IndexEntry]
    flows: list[DataFlow]  # all flows flattened for graph queries


@dataclass
class ValidationIssue:
    component_id: str
    issue: str
    severity: Literal["error", "warning"]
```

- [ ] **Step 3: Create pathfinder/__init__.py**

```python
"""Pathfinder — Architecture-first component library."""
```

- [ ] **Step 4: Create pathfinder/core/__init__.py**

```python
```

- [ ] **Step 5: Create pathfinder/cli/__init__.py**

```python
```

- [ ] **Step 6: Create pathfinder/cli/main.py with click group skeleton**

```python
"""Pathfinder CLI entry point."""

import click


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Architecture-first component library CLI."""
    pass


if __name__ == "__main__":
    cli()
```

- [ ] **Step 7: Create empty test __init__.py files**

Create `tests/__init__.py`, `tests/core/__init__.py`, `tests/cli/__init__.py` as empty files.

- [ ] **Step 8: Install dependencies**

Run: `pip install -e ".[dev]"`
Expected: Package installed in editable mode

- [ ] **Step 9: Verify CLI runs**

Run: `pathfinder --help`
Expected: Shows help with "Architecture-first component library CLI"

- [ ] **Step 10: Commit**

```bash
git init
echo "__pycache__/\n*.egg-info/\ndist/\n.pathfinder/\n.venv/" > .gitignore
git add pyproject.toml pathfinder/ tests/ .gitignore
git commit -m "feat: project scaffolding with types and CLI skeleton"
```

---

### Task 2: Storage Layer

**Files:**
- Create: `pathfinder/core/storage.py`
- Create: `tests/core/test_storage.py`

- [ ] **Step 1: Write failing tests for storage**

```python
# tests/core/test_storage.py
import tempfile
import shutil
from pathlib import Path

import pytest

from pathfinder.core.storage import (
    init_project,
    load_config,
    save_config,
    load_component,
    save_component,
    delete_component,
    load_standards,
    save_standards,
    find_all_component_files,
    get_component_dir,
    get_pathfinder_dir,
)
from pathfinder.types import ProjectConfig, Standards


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestInitProject:
    def test_creates_pathfinder_directory(self, test_dir):
        init_project(test_dir, "Test Project")
        pf_dir = test_dir / ".pathfinder"
        assert pf_dir.exists()
        assert (pf_dir / "config.yaml").exists()
        assert (pf_dir / "components").exists()

    def test_writes_config_with_project_name(self, test_dir):
        init_project(test_dir, "My App")
        config = load_config(test_dir)
        assert config.name == "My App"

    def test_throws_if_already_initialized(self, test_dir):
        init_project(test_dir, "Test")
        with pytest.raises(Exception, match="already initialized"):
            init_project(test_dir, "Test")


class TestConfig:
    def test_saves_and_loads_config(self, test_dir):
        init_project(test_dir, "Test")
        save_config(test_dir, ProjectConfig(
            name="Updated",
            repos={"backend": {"path": "../backend"}},
        ))
        config = load_config(test_dir)
        assert config.name == "Updated"
        assert config.repos["backend"]["path"] == "../backend"

    def test_throws_if_not_initialized(self, test_dir):
        with pytest.raises(Exception, match="not initialized"):
            load_config(test_dir)


class TestComponents:
    @pytest.fixture(autouse=True)
    def setup(self, test_dir):
        init_project(test_dir, "Test")

    def test_saves_and_loads_root_component(self, test_dir):
        save_component(test_dir, {
            "id": "system",
            "name": "My System",
            "type": "system",
            "status": "active",
        })
        comp = load_component(test_dir, "system")
        assert comp["id"] == "system"
        assert comp["name"] == "My System"

    def test_saves_and_loads_nested_component(self, test_dir):
        save_component(test_dir, {
            "id": "payment",
            "name": "Payment Module",
            "type": "module",
            "status": "active",
            "parent": "system",
        })
        save_component(test_dir, {
            "id": "payment.gateway",
            "name": "Payment Gateway",
            "type": "service",
            "status": "active",
            "parent": "payment",
        })
        comp = load_component(test_dir, "payment.gateway")
        assert comp["name"] == "Payment Gateway"
        assert comp["parent"] == "payment"

    def test_creates_directory_hierarchy(self, test_dir):
        save_component(test_dir, {
            "id": "payment",
            "name": "Payment",
            "type": "module",
            "status": "active",
        })
        save_component(test_dir, {
            "id": "payment.gateway",
            "name": "Gateway",
            "type": "service",
            "status": "active",
            "parent": "payment",
        })
        gateway_dir = get_component_dir(test_dir, "payment.gateway")
        assert (gateway_dir / "_component.yaml").exists()
        assert "payment" in str(gateway_dir) and "gateway" in str(gateway_dir)

    def test_deletes_component(self, test_dir):
        save_component(test_dir, {
            "id": "payment",
            "name": "Payment",
            "type": "module",
            "status": "active",
        })
        delete_component(test_dir, "payment")
        with pytest.raises(Exception):
            load_component(test_dir, "payment")

    def test_finds_all_component_files(self, test_dir):
        save_component(test_dir, {
            "id": "system",
            "name": "System",
            "type": "system",
            "status": "active",
        })
        save_component(test_dir, {
            "id": "payment",
            "name": "Payment",
            "type": "module",
            "status": "active",
            "parent": "system",
        })
        files = find_all_component_files(test_dir)
        assert len(files) == 2


class TestStandards:
    @pytest.fixture(autouse=True)
    def setup(self, test_dir):
        init_project(test_dir, "Test")

    def test_saves_and_loads_standards(self, test_dir):
        save_standards(test_dir, {"spec": "Use Python\nUse pytest"})
        standards = load_standards(test_dir)
        assert "Python" in standards["spec"]

    def test_returns_none_when_no_standards(self, test_dir):
        standards = load_standards(test_dir)
        assert standards is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_storage.py`
Expected: FAIL — module not found

- [ ] **Step 3: Implement storage module**

```python
# pathfinder/core/storage.py
"""Storage layer for YAML component files."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml


def get_pathfinder_dir(project_root: Path) -> Path:
    return Path(project_root) / ".pathfinder"


def get_components_dir(project_root: Path) -> Path:
    return get_pathfinder_dir(project_root) / "components"


def _assert_initialized(project_root: Path) -> None:
    if not get_pathfinder_dir(project_root).exists():
        raise RuntimeError(
            f"Pathfinder not initialized in {project_root}. Run 'pathfinder init' first."
        )


def _assert_not_initialized(project_root: Path) -> None:
    if get_pathfinder_dir(project_root).exists():
        raise RuntimeError(f"Pathfinder already initialized in {project_root}.")


def _id_to_path(component_id: str) -> str:
    """Convert component ID to relative path. 'payment.gateway' -> 'payment/gateway'"""
    return component_id.replace(".", "/")


def get_component_dir(project_root: Path, component_id: str) -> Path:
    return get_components_dir(project_root) / _id_to_path(component_id)


def init_project(project_root: Path, name: str) -> None:
    project_root = Path(project_root)
    _assert_not_initialized(project_root)
    pf_dir = get_pathfinder_dir(project_root)
    pf_dir.mkdir(parents=True, exist_ok=True)
    (pf_dir / "components").mkdir(exist_ok=True)
    save_config(project_root, {"name": name})


def load_config(project_root: Path) -> dict:
    project_root = Path(project_root)
    _assert_initialized(project_root)
    config_path = get_pathfinder_dir(project_root) / "config.yaml"
    return yaml.safe_load(config_path.read_text())


def save_config(project_root: Path, config: dict) -> None:
    project_root = Path(project_root)
    pf_dir = get_pathfinder_dir(project_root)
    pf_dir.mkdir(parents=True, exist_ok=True)
    config_path = pf_dir / "config.yaml"
    config_path.write_text(yaml.dump(config, default_flow_style=False))


def load_component(project_root: Path, component_id: str) -> dict:
    project_root = Path(project_root)
    _assert_initialized(project_root)
    comp_dir = get_component_dir(project_root, component_id)
    file_path = comp_dir / "_component.yaml"
    if not file_path.exists():
        raise FileNotFoundError(f"Component '{component_id}' not found at {file_path}")
    return yaml.safe_load(file_path.read_text())


def save_component(project_root: Path, component: dict) -> None:
    project_root = Path(project_root)
    _assert_initialized(project_root)
    comp_dir = get_component_dir(project_root, component["id"])
    comp_dir.mkdir(parents=True, exist_ok=True)
    file_path = comp_dir / "_component.yaml"
    file_path.write_text(yaml.dump(component, default_flow_style=False))


def delete_component(project_root: Path, component_id: str) -> None:
    project_root = Path(project_root)
    _assert_initialized(project_root)
    comp_dir = get_component_dir(project_root, component_id)
    if not comp_dir.exists():
        raise FileNotFoundError(f"Component '{component_id}' not found")
    shutil.rmtree(comp_dir)


def load_standards(project_root: Path) -> dict | None:
    project_root = Path(project_root)
    _assert_initialized(project_root)
    file_path = get_pathfinder_dir(project_root) / "standards.yaml"
    if not file_path.exists():
        return None
    return yaml.safe_load(file_path.read_text())


def save_standards(project_root: Path, standards: dict) -> None:
    project_root = Path(project_root)
    _assert_initialized(project_root)
    file_path = get_pathfinder_dir(project_root) / "standards.yaml"
    file_path.write_text(yaml.dump(standards, default_flow_style=False))


def find_all_component_files(project_root: Path) -> list[Path]:
    project_root = Path(project_root)
    _assert_initialized(project_root)
    components_dir = get_components_dir(project_root)
    if not components_dir.exists():
        return []
    return list(components_dir.rglob("_component.yaml"))


def load_all_components(project_root: Path) -> list[dict]:
    files = find_all_component_files(project_root)
    return [yaml.safe_load(f.read_text()) for f in files]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_storage.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add pathfinder/core/storage.py tests/core/test_storage.py
git commit -m "feat: storage layer for YAML component files"
```

---

### Task 3: Index Builder

**Files:**
- Create: `pathfinder/core/index_builder.py`
- Create: `tests/core/test_index_builder.py`

- [ ] **Step 1: Write failing tests for index builder**

```python
# tests/core/test_index_builder.py
import json
import tempfile
import shutil
from pathlib import Path

import pytest

from pathfinder.core.storage import init_project, save_component
from pathfinder.core.index_builder import build_index, load_index


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_builds_empty_index(test_dir):
    index = build_index(test_dir)
    assert index["version"] == 1
    assert len(index["components"]) == 0
    assert len(index["flows"]) == 0


def test_indexes_parent_child_relationships(test_dir):
    save_component(test_dir, {"id": "system", "name": "System", "type": "system", "status": "active"})
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "module", "status": "active", "parent": "system"})
    save_component(test_dir, {"id": "payment.gateway", "name": "Gateway", "type": "service", "status": "active", "parent": "payment"})

    index = build_index(test_dir)
    assert len(index["components"]) == 3
    assert "payment" in index["components"]["system"]["children"]
    assert "payment.gateway" in index["components"]["payment"]["children"]
    assert len(index["components"]["payment.gateway"]["children"]) == 0


def test_collects_all_data_flows(test_dir):
    save_component(test_dir, {
        "id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "PaymentRequest", "protocol": "REST"}],
    })
    save_component(test_dir, {
        "id": "payment", "name": "Payment", "type": "service", "status": "active",
        "dataFlows": [{"to": "ledger", "data": "Transaction", "protocol": "async/event"}],
    })

    index = build_index(test_dir)
    assert len(index["flows"]) == 2


def test_resolves_implicit_from(test_dir):
    save_component(test_dir, {
        "id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "PaymentRequest"}],
    })

    index = build_index(test_dir)
    flow = index["flows"][0]
    assert flow["from"] == "order"
    assert flow["to"] == "payment"


def test_writes_and_loads_index(test_dir):
    save_component(test_dir, {"id": "system", "name": "System", "type": "system", "status": "active"})

    build_index(test_dir)
    index_path = test_dir / ".pathfinder" / "index.json"
    assert index_path.exists()

    loaded = load_index(test_dir)
    assert loaded["components"]["system"]["name"] == "System"


def test_preserves_code_mappings_and_tags(test_dir):
    save_component(test_dir, {
        "id": "payment", "name": "Payment", "type": "service", "status": "active",
        "codeMappings": [{"repo": "backend", "glob": "src/payment/**"}],
        "tags": ["pci-scope"],
    })

    index = build_index(test_dir)
    assert len(index["components"]["payment"]["codeMappings"]) == 1
    assert "pci-scope" in index["components"]["payment"]["tags"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_index_builder.py`
Expected: FAIL — module not found

- [ ] **Step 3: Implement index builder**

```python
# pathfinder/core/index_builder.py
"""Build and manage the index.json graph index."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pathfinder.core.storage import (
    load_all_components,
    find_all_component_files,
    get_pathfinder_dir,
    get_component_dir,
)


def build_index(project_root: Path) -> dict:
    project_root = Path(project_root)
    components = load_all_components(project_root)

    # Build component map
    entries: dict[str, dict] = {}
    for comp in components:
        comp_id = comp["id"]
        entries[comp_id] = {
            "id": comp_id,
            "name": comp["name"],
            "type": comp["type"],
            "status": comp["status"],
            "parent": comp.get("parent"),
            "children": [],
            "tags": comp.get("tags", []),
            "dataFlows": comp.get("dataFlows", []),
            "codeMappings": comp.get("codeMappings", []),
            "filePath": str(get_component_dir(project_root, comp_id) / "_component.yaml"),
        }

    # Resolve parent-child relationships
    for entry in entries.values():
        parent = entry.get("parent")
        if parent and parent in entries:
            entries[parent]["children"].append(entry["id"])

    # Collect all flows, resolving implicit 'from' to owning component
    flows: list[dict] = []
    for comp in components:
        for flow in comp.get("dataFlows", []):
            flows.append({
                "from": flow.get("from", comp["id"]),
                "to": flow.get("to"),
                "data": flow["data"],
                "protocol": flow.get("protocol"),
            })

    index = {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "components": entries,
        "flows": flows,
    }

    # Write index.json
    index_path = get_pathfinder_dir(project_root) / "index.json"
    index_path.write_text(json.dumps(index, indent=2))

    return index


def load_index(project_root: Path) -> dict:
    project_root = Path(project_root)
    index_path = get_pathfinder_dir(project_root) / "index.json"
    if not index_path.exists():
        raise FileNotFoundError("Index not found. Run any query command to rebuild.")
    return json.loads(index_path.read_text())


def is_index_stale(project_root: Path) -> bool:
    project_root = Path(project_root)
    index_path = get_pathfinder_dir(project_root) / "index.json"
    if not index_path.exists():
        return True
    index_mtime = index_path.stat().st_mtime
    for f in find_all_component_files(project_root):
        if f.stat().st_mtime > index_mtime:
            return True
    return False


def ensure_index(project_root: Path) -> dict:
    if is_index_stale(project_root):
        return build_index(project_root)
    return load_index(project_root)


def validate_index(project_root: Path) -> list[dict]:
    project_root = Path(project_root)
    index = build_index(project_root)
    issues: list[dict] = []

    for comp in index["components"].values():
        # Check parent references
        parent = comp.get("parent")
        if parent and parent not in index["components"]:
            issues.append({
                "component_id": comp["id"],
                "issue": f"Parent '{parent}' does not exist",
                "severity": "error",
            })

        # Check data flow references
        for flow in comp.get("dataFlows", []):
            if flow.get("to") and flow["to"] not in index["components"]:
                issues.append({
                    "component_id": comp["id"],
                    "issue": f"Data flow references unknown component '{flow['to']}'",
                    "severity": "error",
                })
            flow_from = flow.get("from")
            if flow_from and flow_from != comp["id"] and flow_from not in index["components"]:
                issues.append({
                    "component_id": comp["id"],
                    "issue": f"Data flow references unknown component '{flow_from}'",
                    "severity": "error",
                })

        # Check ID matches folder path
        expected_dir = get_component_dir(project_root, comp["id"])
        actual_dir = Path(comp["filePath"]).parent
        if expected_dir.resolve() != actual_dir.resolve():
            issues.append({
                "component_id": comp["id"],
                "issue": f"ID '{comp['id']}' does not match folder path",
                "severity": "error",
            })

    # Check for duplicate IDs
    all_components = load_all_components(project_root)
    id_counts: dict[str, int] = {}
    for comp in all_components:
        id_counts[comp["id"]] = id_counts.get(comp["id"], 0) + 1
    for comp_id, count in id_counts.items():
        if count > 1:
            issues.append({
                "component_id": comp_id,
                "issue": f"Duplicate component ID (found {count} times)",
                "severity": "error",
            })

    return issues
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_index_builder.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add pathfinder/core/index_builder.py tests/core/test_index_builder.py
git commit -m "feat: index builder - YAML to JSON graph index"
```

---

### Task 4: Graph Operations

**Files:**
- Create: `pathfinder/core/graph.py`
- Create: `tests/core/test_graph.py`

- [ ] **Step 1: Write failing tests for graph operations**

```python
# tests/core/test_graph.py
import tempfile
import shutil
from pathlib import Path
from collections import deque

import pytest

from pathfinder.core.storage import init_project, save_component
from pathfinder.core.index_builder import build_index
from pathfinder.core.graph import (
    get_dependencies,
    get_dependents,
    get_flows_for_component,
    trace_flow,
    get_components_by_tag,
    find_component_by_code_path,
)


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def graph_index(test_dir):
    save_component(test_dir, {
        "id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "PaymentRequest", "protocol": "REST"}],
        "codeMappings": [{"glob": "src/order/**"}],
    })
    save_component(test_dir, {
        "id": "payment", "name": "Payment", "type": "service", "status": "active",
        "dataFlows": [{"to": "ledger", "data": "Transaction", "protocol": "async/event"}],
        "codeMappings": [{"repo": "backend", "glob": "src/payment/**"}],
        "tags": ["pci-scope"],
    })
    save_component(test_dir, {
        "id": "ledger", "name": "Ledger", "type": "service", "status": "active",
        "codeMappings": [{"glob": "src/ledger/**"}],
        "tags": ["pci-scope"],
    })
    save_component(test_dir, {
        "id": "notification", "name": "Notification", "type": "service", "status": "active",
        "dataFlows": [{"from": "payment", "data": "PaymentEvent"}],
    })
    return build_index(test_dir)


class TestGetDependencies:
    def test_returns_outgoing_deps(self, graph_index):
        deps = get_dependencies(graph_index, "order")
        assert "payment" in deps
        assert "ledger" not in deps

    def test_returns_empty_for_leaf(self, graph_index):
        deps = get_dependencies(graph_index, "ledger")
        assert len(deps) == 0


class TestGetDependents:
    def test_returns_incoming_deps(self, graph_index):
        dependents = get_dependents(graph_index, "payment")
        assert "order" in dependents


class TestGetFlowsForComponent:
    def test_returns_all_flows(self, graph_index):
        flows = get_flows_for_component(graph_index, "payment")
        assert len(flows) >= 2


class TestTraceFlow:
    def test_finds_path(self, graph_index):
        path = trace_flow(graph_index, "order", "ledger")
        assert path == ["order", "payment", "ledger"]

    def test_returns_none_when_no_path(self, graph_index):
        path = trace_flow(graph_index, "ledger", "order")
        assert path is None


class TestGetComponentsByTag:
    def test_finds_tagged(self, graph_index):
        tagged = get_components_by_tag(graph_index, "pci-scope")
        assert "payment" in tagged
        assert "ledger" in tagged
        assert "order" not in tagged


class TestFindComponentByCodePath:
    def test_finds_owner(self, graph_index):
        comp = find_component_by_code_path(graph_index, "src/payment/gateway/handler.py")
        assert comp == "payment"

    def test_returns_none_for_unmapped(self, graph_index):
        comp = find_component_by_code_path(graph_index, "src/unknown/file.py")
        assert comp is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_graph.py`
Expected: FAIL — module not found

- [ ] **Step 3: Implement graph operations**

```python
# pathfinder/core/graph.py
"""Graph operations: deps, dependents, trace, flow queries."""

from __future__ import annotations

from collections import deque
from fnmatch import fnmatch


def get_dependencies(index: dict, component_id: str) -> list[str]:
    """Get component IDs that this component sends data TO."""
    deps = set()
    for flow in index["flows"]:
        if flow.get("from") == component_id and flow.get("to"):
            deps.add(flow["to"])
    return list(deps)


def get_dependents(index: dict, component_id: str) -> list[str]:
    """Get component IDs that send data TO this component."""
    dependents = set()
    for flow in index["flows"]:
        if flow.get("to") == component_id and flow.get("from"):
            dependents.add(flow["from"])
    return list(dependents)


def get_flows_for_component(index: dict, component_id: str) -> list[dict]:
    """Get all flows where this component is source or target."""
    return [
        f for f in index["flows"]
        if f.get("from") == component_id or f.get("to") == component_id
    ]


def trace_flow(index: dict, from_id: str, to_id: str) -> list[str] | None:
    """BFS to find shortest path between two components through data flows."""
    if from_id == to_id:
        return [from_id]

    # Build adjacency list
    adj: dict[str, set[str]] = {}
    for flow in index["flows"]:
        src = flow.get("from")
        dst = flow.get("to")
        if src and dst:
            adj.setdefault(src, set()).add(dst)

    # BFS
    visited = {from_id}
    parent: dict[str, str] = {}
    queue = deque([from_id])

    while queue:
        current = queue.popleft()
        for neighbor in adj.get(current, set()):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            parent[neighbor] = current

            if neighbor == to_id:
                # Reconstruct path
                path = [to_id]
                node = to_id
                while node in parent:
                    node = parent[node]
                    path.append(node)
                path.reverse()
                return path

            queue.append(neighbor)

    return None


def get_components_by_tag(index: dict, tag: str) -> list[str]:
    """Find all components with a specific tag."""
    return [
        comp["id"]
        for comp in index["components"].values()
        if tag in comp.get("tags", [])
    ]


def find_component_by_code_path(index: dict, file_path: str) -> str | None:
    """Find which component owns a given file path using glob matching."""
    best_match = None
    best_specificity = 0

    for comp in index["components"].values():
        for mapping in comp.get("codeMappings", []):
            if fnmatch(file_path, mapping["glob"]):
                specificity = len(mapping["glob"])
                if specificity > best_specificity:
                    best_specificity = specificity
                    best_match = comp["id"]

    return best_match
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_graph.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add pathfinder/core/graph.py tests/core/test_graph.py
git commit -m "feat: graph operations - deps, flows, trace, tag queries"
```

---

### Task 5: CLI — init command

**Files:**
- Create: `pathfinder/cli/init_cmd.py`
- Create: `pathfinder/cli/utils.py`
- Create: `tests/cli/test_init.py`
- Modify: `pathfinder/cli/main.py`

- [ ] **Step 1: Write failing test for init**

```python
# tests/cli/test_init.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_creates_pathfinder_directory(runner, test_dir):
    result = runner.invoke(cli, ["init", "--name", "Test Project", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert (test_dir / ".pathfinder").exists()
    assert "Initialized" in result.output


def test_fails_if_already_initialized(runner, test_dir):
    runner.invoke(cli, ["init", "--name", "Test", "--root", str(test_dir)])
    result = runner.invoke(cli, ["init", "--name", "Test", "--root", str(test_dir)])
    assert result.exit_code != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_init.py`
Expected: FAIL

- [ ] **Step 3: Create CLI utils**

```python
# pathfinder/cli/utils.py
"""Shared CLI utilities."""

from pathlib import Path
import os


def resolve_root(root: str | None) -> Path:
    if root:
        return Path(root).resolve()
    env_root = os.environ.get("PATHFINDER_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd()
```

- [ ] **Step 4: Implement init command**

```python
# pathfinder/cli/init_cmd.py
"""Init command."""

import click

from pathfinder.core.storage import init_project
from pathfinder.cli.utils import resolve_root


@click.command("init")
@click.option("--name", required=True, help="Project name")
@click.option("--root", default=None, help="Project root directory")
def init_cmd(name: str, root: str | None):
    """Initialize a new Pathfinder project."""
    project_root = resolve_root(root)
    try:
        init_project(project_root, name)
        click.echo(f"Initialized Pathfinder project '{name}' in {project_root}/.pathfinder/")
    except RuntimeError as e:
        raise click.ClickException(str(e))
```

- [ ] **Step 5: Wire init into CLI main**

```python
# pathfinder/cli/main.py
"""Pathfinder CLI entry point."""

import click

from pathfinder.cli.init_cmd import init_cmd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Architecture-first component library CLI."""
    pass


cli.add_command(init_cmd)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/cli/test_init.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add pathfinder/cli/main.py pathfinder/cli/init_cmd.py pathfinder/cli/utils.py tests/cli/test_init.py
git commit -m "feat: CLI init command"
```

---

### Task 6: CLI — add, remove, move commands

**Files:**
- Create: `pathfinder/cli/add_cmd.py`
- Create: `pathfinder/cli/remove_cmd.py`
- Create: `pathfinder/cli/move_cmd.py`
- Create: `tests/cli/test_add.py`
- Create: `tests/cli/test_remove.py`
- Create: `tests/cli/test_move.py`
- Modify: `pathfinder/cli/main.py`

- [ ] **Step 1: Write failing tests for add**

```python
# tests/cli/test_add.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import load_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    runner = CliRunner()
    runner.invoke(cli, ["init", "--name", "Test", "--root", str(d)])
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_adds_root_component(runner, test_dir):
    result = runner.invoke(cli, ["add", "system", "My System", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert "Added" in result.output
    comp = load_component(test_dir, "my-system")
    assert comp["name"] == "My System"
    assert comp["type"] == "system"


def test_adds_child_with_parent(runner, test_dir):
    runner.invoke(cli, ["add", "system", "System", "--root", str(test_dir)])
    runner.invoke(cli, ["add", "module", "Payment", "--parent", "system", "--root", str(test_dir)])
    comp = load_component(test_dir, "system.payment")
    assert comp["parent"] == "system"


def test_adds_nested_child(runner, test_dir):
    runner.invoke(cli, ["add", "system", "System", "--root", str(test_dir)])
    runner.invoke(cli, ["add", "module", "Payment", "--parent", "system", "--root", str(test_dir)])
    runner.invoke(cli, ["add", "service", "Gateway", "--parent", "system.payment", "--root", str(test_dir)])
    comp = load_component(test_dir, "system.payment.gateway")
    assert comp["parent"] == "system.payment"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_add.py`
Expected: FAIL

- [ ] **Step 3: Implement add command**

```python
# pathfinder/cli/add_cmd.py
"""Add command."""

import re
import click

from pathfinder.core.storage import save_component, load_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


def name_to_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


@click.command("add")
@click.argument("type_", metavar="TYPE")
@click.argument("name")
@click.option("--parent", default=None, help="Parent component ID")
@click.option("--root", default=None, help="Project root directory")
def add_cmd(type_: str, name: str, parent: str | None, root: str | None):
    """Add a new component."""
    project_root = resolve_root(root)
    slug = name_to_slug(name)
    comp_id = f"{parent}.{slug}" if parent else slug

    if parent:
        try:
            load_component(project_root, parent)
        except FileNotFoundError:
            raise click.ClickException(f"Parent component '{parent}' not found")

    save_component(project_root, {
        "id": comp_id,
        "name": name,
        "type": type_,
        "status": "active",
        "parent": parent,
    })

    build_index(project_root)
    click.echo(f"Added {type_} '{name}' ({comp_id})")
```

- [ ] **Step 4: Write failing tests for remove**

```python
# tests/cli/test_remove.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import load_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    runner = CliRunner()
    runner.invoke(cli, ["init", "--name", "Test", "--root", str(d)])
    runner.invoke(cli, ["add", "system", "System", "--root", str(d)])
    runner.invoke(cli, ["add", "module", "Payment", "--parent", "system", "--root", str(d)])
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_removes_leaf_with_force(runner, test_dir):
    result = runner.invoke(cli, ["remove", "system.payment", "--force", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_recursively_removes_children(runner, test_dir):
    runner.invoke(cli, ["add", "service", "Gateway", "--parent", "system.payment", "--root", str(test_dir)])
    result = runner.invoke(cli, ["remove", "system.payment", "--force", "--root", str(test_dir)])
    assert result.exit_code == 0
    with pytest.raises(FileNotFoundError):
        load_component(test_dir, "system.payment.gateway")


def test_dry_run_shows_without_deleting(runner, test_dir):
    runner.invoke(cli, ["add", "service", "Gateway", "--parent", "system.payment", "--root", str(test_dir)])
    result = runner.invoke(cli, ["remove", "system.payment", "--dry-run", "--root", str(test_dir)])
    assert "Would remove" in result.output
    comp = load_component(test_dir, "system.payment")
    assert comp["name"] == "Payment"


def test_blocks_without_force_when_children(runner, test_dir):
    runner.invoke(cli, ["add", "service", "Gateway", "--parent", "system.payment", "--root", str(test_dir)])
    result = runner.invoke(cli, ["remove", "system.payment", "--root", str(test_dir)])
    assert result.exit_code != 0
```

- [ ] **Step 5: Implement remove command**

```python
# pathfinder/cli/remove_cmd.py
"""Remove command."""

import click

from pathfinder.core.storage import delete_component
from pathfinder.core.index_builder import build_index
from pathfinder.core.graph import get_dependents
from pathfinder.cli.utils import resolve_root


def collect_descendants(index: dict, comp_id: str) -> list[str]:
    result = [comp_id]
    entry = index["components"].get(comp_id)
    if entry:
        for child_id in entry.get("children", []):
            result.extend(collect_descendants(index, child_id))
    return result


@click.command("remove")
@click.argument("id_")
@click.option("--force", is_flag=True, help="Skip confirmation and remove")
@click.option("--dry-run", is_flag=True, help="Show what would be removed")
@click.option("--root", default=None, help="Project root directory")
def remove_cmd(id_: str, force: bool, dry_run: bool, root: str | None):
    """Remove a component and its children recursively."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    entry = index["components"].get(id_)

    if not entry:
        raise click.ClickException(f"Component '{id_}' not found")

    to_remove = collect_descendants(index, id_)

    # Find external dependents
    external_dependents = []
    for remove_id in to_remove:
        for dep in get_dependents(index, remove_id):
            if dep not in to_remove and dep not in external_dependents:
                external_dependents.append(dep)

    if dry_run:
        click.echo(f"Would remove {len(to_remove)} component(s):")
        for r in to_remove:
            name = index["components"].get(r, {}).get("name", r)
            click.echo(f"  {name} ({r})")
        if external_dependents:
            click.echo("\nWarning: these components have flows referencing removed components:")
            for dep in external_dependents:
                name = index["components"].get(dep, {}).get("name", dep)
                click.echo(f"  {name} ({dep})")
        return

    if not force and (len(to_remove) > 1 or external_dependents):
        raise click.ClickException(
            f"Component '{id_}' has {len(to_remove) - 1} children and "
            f"{len(external_dependents)} external dependents. "
            f"Use --dry-run to see details, or --force to remove anyway."
        )

    for remove_id in reversed(to_remove):
        delete_component(project_root, remove_id)

    build_index(project_root)
    click.echo(f"Removed {len(to_remove)} component(s) starting from '{id_}'")
```

- [ ] **Step 6: Write failing tests for move**

```python
# tests/cli/test_move.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import load_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    runner = CliRunner()
    runner.invoke(cli, ["init", "--name", "Test", "--root", str(d)])
    runner.invoke(cli, ["add", "system", "System", "--root", str(d)])
    runner.invoke(cli, ["add", "module", "Payment", "--parent", "system", "--root", str(d)])
    runner.invoke(cli, ["add", "module", "Billing", "--parent", "system", "--root", str(d)])
    runner.invoke(cli, ["add", "service", "Gateway", "--parent", "system.payment", "--root", str(d)])
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_moves_component_to_new_parent(runner, test_dir):
    result = runner.invoke(cli, ["move", "system.payment.gateway", "--parent", "system.billing", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert "Moved" in result.output
    comp = load_component(test_dir, "system.billing.gateway")
    assert comp["parent"] == "system.billing"
```

- [ ] **Step 7: Implement move command**

```python
# pathfinder/cli/move_cmd.py
"""Move command."""

import click

from pathfinder.core.storage import load_component, save_component, delete_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("move")
@click.argument("id_")
@click.option("--parent", required=True, help="New parent component ID")
@click.option("--root", default=None, help="Project root directory")
def move_cmd(id_: str, parent: str, root: str | None):
    """Move a component to a new parent."""
    project_root = resolve_root(root)
    component = load_component(project_root, id_)

    # Verify new parent exists
    try:
        load_component(project_root, parent)
    except FileNotFoundError:
        raise click.ClickException(f"Parent component '{parent}' not found")

    # Compute new ID
    slug = id_.rsplit(".", 1)[-1] if "." in id_ else id_
    new_id = f"{parent}.{slug}"

    # Delete old, save new
    delete_component(project_root, id_)
    component["id"] = new_id
    component["parent"] = parent
    save_component(project_root, component)

    build_index(project_root)
    click.echo(f"Moved '{id_}' -> '{new_id}' (parent: {parent})")
```

- [ ] **Step 8: Wire all commands into CLI main**

```python
# pathfinder/cli/main.py
"""Pathfinder CLI entry point."""

import click

from pathfinder.cli.init_cmd import init_cmd
from pathfinder.cli.add_cmd import add_cmd
from pathfinder.cli.remove_cmd import remove_cmd
from pathfinder.cli.move_cmd import move_cmd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Architecture-first component library CLI."""
    pass


cli.add_command(init_cmd)
cli.add_command(add_cmd)
cli.add_command(remove_cmd)
cli.add_command(move_cmd)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 9: Run all tests**

Run: `pytest tests/cli/test_add.py tests/cli/test_remove.py tests/cli/test_move.py -v`
Expected: All tests PASS

- [ ] **Step 10: Commit**

```bash
git add pathfinder/cli/add_cmd.py pathfinder/cli/remove_cmd.py pathfinder/cli/move_cmd.py pathfinder/cli/main.py tests/cli/test_add.py tests/cli/test_remove.py tests/cli/test_move.py
git commit -m "feat: CLI add, remove, move commands"
```

---

### Task 7: CLI — list, show, children commands

**Files:**
- Create: `pathfinder/cli/list_cmd.py`
- Create: `pathfinder/cli/show_cmd.py`
- Create: `tests/cli/test_list.py`
- Create: `tests/cli/test_show.py`
- Modify: `pathfinder/cli/main.py`

- [ ] **Step 1: Write failing tests for list**

```python
# tests/cli/test_list.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    runner = CliRunner()
    runner.invoke(cli, ["init", "--name", "Test", "--root", str(d)])
    runner.invoke(cli, ["add", "system", "System", "--root", str(d)])
    runner.invoke(cli, ["add", "module", "Payment", "--parent", "system", "--root", str(d)])
    runner.invoke(cli, ["add", "service", "Gateway", "--parent", "system.payment", "--root", str(d)])
    runner.invoke(cli, ["add", "module", "Auth", "--parent", "system", "--root", str(d)])
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_shows_tree(runner, test_dir):
    result = runner.invoke(cli, ["list", "--root", str(test_dir)])
    assert "System" in result.output
    assert "Payment" in result.output
    assert "Gateway" in result.output
    assert "Auth" in result.output


def test_truncates_at_level(runner, test_dir):
    result = runner.invoke(cli, ["list", "--level", "1", "--root", str(test_dir)])
    assert "System" in result.output
    assert "Payment" in result.output
    assert "Gateway" not in result.output
```

- [ ] **Step 2: Implement list command**

```python
# pathfinder/cli/list_cmd.py
"""List command — tree view."""

import click

from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


def print_tree(index, comp_id, prefix, is_last, max_level, current_level):
    entry = index["components"].get(comp_id)
    if not entry:
        return

    connector = "" if prefix == "" else ("└── " if is_last else "├── ")
    type_tag = f"[{entry['type']}]"
    status_tag = f" ({entry['status']})" if entry["status"] != "active" else ""
    click.echo(f"{prefix}{connector}{entry['name']} {type_tag}{status_tag}")

    if max_level > 0 and current_level >= max_level:
        return

    children = entry.get("children", [])
    child_prefix = "" if prefix == "" else prefix + ("    " if is_last else "│   ")
    for i, child_id in enumerate(children):
        print_tree(index, child_id, child_prefix, i == len(children) - 1, max_level, current_level + 1)


@click.command("list")
@click.option("--level", type=int, default=0, help="Maximum depth to show")
@click.option("--root", default=None, help="Project root directory")
def list_cmd(level: int, root: str | None):
    """Show component tree."""
    project_root = resolve_root(root)
    index = build_index(project_root)

    roots = [c for c in index["components"].values() if not c.get("parent")]

    if not roots:
        click.echo("No components defined. Use 'pathfinder add' to create one.")
        return

    for i, root_comp in enumerate(roots):
        print_tree(index, root_comp["id"], "", i == len(roots) - 1, level, 1)
```

- [ ] **Step 3: Write failing tests for show and children**

```python
# tests/cli/test_show.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {
        "id": "payment", "name": "Payment", "type": "module", "status": "active",
        "spec": "Handles all payment processing",
        "contracts": {
            "inputs": [{"name": "ProcessPayment", "format": "POST /api/payments", "source": "order"}],
            "outputs": [{"name": "PaymentResult", "format": "{ status }", "target": "order"}],
        },
        "dataFlows": [{"to": "ledger", "data": "Transaction", "protocol": "async"}],
        "tags": ["pci-scope"],
    })
    save_component(d, {
        "id": "payment.gateway", "name": "Gateway", "type": "service",
        "status": "active", "parent": "payment",
    })
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_shows_full_details(runner, test_dir):
    result = runner.invoke(cli, ["show", "payment", "--root", str(test_dir)])
    assert "Payment" in result.output
    assert "Handles all payment processing" in result.output
    assert "pci-scope" in result.output


def test_shows_only_contracts(runner, test_dir):
    result = runner.invoke(cli, ["show", "payment", "--contracts", "--root", str(test_dir)])
    assert "ProcessPayment" in result.output
    assert "PaymentResult" in result.output


def test_children_lists_direct_children(runner, test_dir):
    result = runner.invoke(cli, ["children", "payment", "--root", str(test_dir)])
    assert "Gateway" in result.output
```

- [ ] **Step 4: Implement show command**

```python
# pathfinder/cli/show_cmd.py
"""Show and children commands."""

import click

from pathfinder.core.storage import load_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("show")
@click.argument("id_")
@click.option("--contracts", is_flag=True, help="Show only contracts")
@click.option("--root", default=None, help="Project root directory")
def show_cmd(id_: str, contracts: bool, root: str | None):
    """Show component details."""
    project_root = resolve_root(root)
    component = load_component(project_root, id_)

    if contracts:
        click.echo(f"Contracts for {component['name']} ({component['id']}):")
        c = component.get("contracts", {})
        for inp in c.get("inputs", []):
            source = f" (from: {inp['source']})" if inp.get("source") else ""
            click.echo(f"\n  Input: {inp['name']}{source}")
            click.echo(f"    {inp['format'].strip()}")
        for out in c.get("outputs", []):
            target = f" (to: {out['target']})" if out.get("target") else ""
            click.echo(f"\n  Output: {out['name']}{target}")
            click.echo(f"    {out['format'].strip()}")
        return

    click.echo(f"{component['name']} [{component['type']}] ({component['status']})")
    click.echo(f"ID: {component['id']}")
    if component.get("parent"):
        click.echo(f"Parent: {component['parent']}")
    if component.get("tags"):
        click.echo(f"Tags: {', '.join(component['tags'])}")
    if component.get("spec"):
        lines = component["spec"].strip().split("\n")
        click.echo(f"\nSpec:\n  " + "\n  ".join(lines))
    c = component.get("contracts", {})
    for inp in c.get("inputs", []):
        click.echo(f"\nContract (input): {inp['name']}")
    for out in c.get("outputs", []):
        click.echo(f"\nContract (output): {out['name']}")
    for flow in component.get("dataFlows", []):
        direction = f"→ {flow['to']}" if flow.get("to") else f"← {flow.get('from')}"
        protocol = f" [{flow['protocol']}]" if flow.get("protocol") else ""
        click.echo(f"\nFlow: {direction}: {flow['data']}{protocol}")
    for mapping in component.get("codeMappings", []):
        repo = f"{mapping['repo']}:" if mapping.get("repo") else ""
        click.echo(f"\nCode: {repo}{mapping['glob']}")


@click.command("children")
@click.argument("id_")
@click.option("--root", default=None, help="Project root directory")
def children_cmd(id_: str, root: str | None):
    """List direct children of a component."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    entry = index["components"].get(id_)

    if not entry:
        raise click.ClickException(f"Component '{id_}' not found")

    children = entry.get("children", [])
    if not children:
        click.echo(f"{entry['name']} has no children")
        return

    click.echo(f"Children of {entry['name']}:")
    for child_id in children:
        child = index["components"][child_id]
        click.echo(f"  {child['name']} [{child['type']}] ({child_id})")
```

- [ ] **Step 5: Wire into CLI main and run tests**

Add imports and `cli.add_command(list_cmd)`, `cli.add_command(show_cmd)`, `cli.add_command(children_cmd)` to `main.py`.

Run: `pytest tests/cli/test_list.py tests/cli/test_show.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add pathfinder/cli/list_cmd.py pathfinder/cli/show_cmd.py pathfinder/cli/main.py tests/cli/test_list.py tests/cli/test_show.py
git commit -m "feat: CLI list, show, children commands"
```

---

### Task 8-12: Remaining CLI Commands

Tasks 8-12 follow the same pattern. For each command group:
1. Write pytest tests using `CliRunner`
2. Run to verify failure
3. Implement the click command
4. Wire into `main.py`
5. Run tests to verify pass
6. Commit

**Task 8: deps + dependents** (`deps_cmd.py`, `test_deps.py`)
**Task 9: flows + flow-add + trace** (`flows_cmd.py`, `test_flows.py`)
**Task 10: map + unmapped + mapped** (`map_cmd.py`, `test_map.py`)
**Task 11: drift check with --ci** (`drift_cmd.py`, `test_drift.py`)
**Task 12: standards + export** (`standards_cmd.py`, `export_cmd.py`, `test_standards.py`, `test_export.py`)

Each follows the identical test/implement/wire/commit pattern from Tasks 5-7. The implementation logic is the same as described in the design spec — only the language changes from TypeScript to Python. Tests use `click.testing.CliRunner` and `pytest` fixtures.

Key implementation notes per command:

**deps_cmd.py:**
```python
@click.command("deps")
@click.argument("id_")
@click.option("--root", default=None)
def deps_cmd(id_, root):
    # Uses graph.get_dependencies(index, id_)

@click.command("dependents")
@click.argument("id_")
@click.option("--root", default=None)
def dependents_cmd(id_, root):
    # Uses graph.get_dependents(index, id_)
```

**flows_cmd.py:**
```python
@click.command("flows")
@click.argument("id_", required=False)
@click.option("--root", default=None)
def flows_cmd(id_, root):
    # Shows all flows or flows for a specific component

@click.command("trace")
@click.argument("from_id")
@click.argument("to_id")
@click.option("--root", default=None)
def trace_cmd(from_id, to_id, root):
    # Uses graph.trace_flow(index, from_id, to_id)

@click.command("flow-add")
@click.argument("from_id")
@click.argument("to_id")
@click.option("--data", required=True)
@click.option("--protocol", default=None)
@click.option("--root", default=None)
def flow_add_cmd(from_id, to_id, data, protocol, root):
    # Loads component, appends to dataFlows, saves
```

**map_cmd.py:**
```python
@click.command("map")
@click.argument("id_")
@click.option("--glob", "glob_pattern", required=True)
@click.option("--repo", default=None)
@click.option("--root", default=None)
def map_cmd(id_, glob_pattern, repo, root):
    # Loads component, appends to codeMappings, saves

@click.command("mapped")
@click.argument("file")
@click.option("--root", default=None)
def mapped_cmd(file, root):
    # Uses graph.find_component_by_code_path(index, file)

@click.command("unmapped")
@click.option("--root", default=None)
def unmapped_cmd(root):
    # Lists components with no codeMappings
```

**drift_cmd.py:**
```python
@click.group("drift")
def drift_group():
    pass

@drift_group.command("check")
@click.option("--ci", is_flag=True, help="Exit code 1 if drift found")
@click.option("--root", default=None)
def drift_check_cmd(ci, root):
    # Checks: no code mappings, empty globs, broken flow refs
    # Uses glob.glob() to verify file patterns match
    # If ci and issues: sys.exit(1)
```

**export_cmd.py:**
```python
@click.command("export")
@click.option("--format", "fmt", required=True, type=click.Choice(["json", "dot", "markdown"]))
@click.option("--root", default=None)
def export_cmd(fmt, root):
    # json: json.dumps(index, indent=2)
    # dot: digraph with nodes and edges
    # markdown: hierarchical markdown doc
```

---

### Task 13: CLI — set command

**Files:**
- Create: `pathfinder/cli/set_cmd.py`
- Create: `tests/cli/test_set.py`
- Modify: `pathfinder/cli/main.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/cli/test_set.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component, load_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {
        "id": "payment", "name": "Payment", "type": "service",
        "status": "active", "tags": ["existing-tag"],
    })
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_updates_status(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--status", "deprecated", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert comp["status"] == "deprecated"


def test_adds_tag(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--tag", "pci-scope", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert "pci-scope" in comp["tags"]
    assert "existing-tag" in comp["tags"]


def test_updates_type(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--type", "module", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert comp["type"] == "module"


def test_removes_tag(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--remove-tag", "existing-tag", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert "existing-tag" not in comp.get("tags", [])
```

- [ ] **Step 2: Implement set command**

```python
# pathfinder/cli/set_cmd.py
"""Set command — update component fields."""

import click

from pathfinder.core.storage import load_component, save_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("set")
@click.argument("id_")
@click.option("--status", default=None, help="Set status (proposed, active, deprecated)")
@click.option("--type", "type_", default=None, help="Set type")
@click.option("--tag", default=None, help="Add a tag")
@click.option("--remove-tag", default=None, help="Remove a tag")
@click.option("--root", default=None, help="Project root directory")
def set_cmd(id_: str, status, type_, tag, remove_tag, root):
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

    if not changes:
        click.echo("No changes specified")
        return

    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Updated {component['name']} ({id_}): {', '.join(changes)}")
```

- [ ] **Step 3: Wire into CLI and run tests**

Run: `pytest tests/cli/test_set.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add pathfinder/cli/set_cmd.py tests/cli/test_set.py pathfinder/cli/main.py
git commit -m "feat: CLI set command for updating component fields"
```

---

### Task 14: CLI — info command

**Files:**
- Create: `pathfinder/cli/info_cmd.py`
- Create: `tests/cli/test_info.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/cli/test_info.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test Project")
    save_component(d, {"id": "system", "name": "System", "type": "system", "status": "active"})
    save_component(d, {"id": "payment", "name": "Payment", "type": "module", "status": "active", "parent": "system",
                        "dataFlows": [{"to": "ledger", "data": "Transaction"}]})
    save_component(d, {"id": "ledger", "name": "Ledger", "type": "service", "status": "active", "parent": "system"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_shows_project_summary(runner, test_dir):
    result = runner.invoke(cli, ["info", "--root", str(test_dir)])
    assert "Test Project" in result.output
    assert "3" in result.output  # component count
    assert "1" in result.output  # flow count
```

- [ ] **Step 2: Implement info command**

```python
# pathfinder/cli/info_cmd.py
"""Info command — project summary."""

import click

from pathfinder.core.storage import load_config
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("info")
@click.option("--root", default=None, help="Project root directory")
def info_cmd(root: str | None):
    """Show project summary."""
    project_root = resolve_root(root)
    config = load_config(project_root)
    index = build_index(project_root)

    components = list(index["components"].values())
    by_type: dict[str, int] = {}
    tags: set[str] = set()

    for comp in components:
        by_type[comp["type"]] = by_type.get(comp["type"], 0) + 1
        for t in comp.get("tags", []):
            tags.add(t)

    click.echo(f"Project: {config['name']}")
    click.echo(f"Components: {len(components)}")
    click.echo(f"Data flows: {len(index['flows'])}")

    if by_type:
        click.echo("\nBy type:")
        for type_, count in by_type.items():
            click.echo(f"  {type_}: {count}")

    if tags:
        click.echo(f"\nTags: {', '.join(sorted(tags))}")

    repos = config.get("repos", {})
    if repos:
        click.echo(f"\nRepos: {', '.join(repos.keys())}")
```

- [ ] **Step 3: Wire into CLI and run tests**

Run: `pytest tests/cli/test_info.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add pathfinder/cli/info_cmd.py tests/cli/test_info.py pathfinder/cli/main.py
git commit -m "feat: CLI info command for project summary"
```

---

### Task 15: CLI — search command

**Files:**
- Create: `pathfinder/cli/search_cmd.py`
- Create: `tests/cli/test_search.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/cli/test_search.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "payment", "name": "Payment Gateway", "type": "service", "status": "active", "tags": ["pci-scope", "customer-facing"]})
    save_component(d, {"id": "auth", "name": "Auth Service", "type": "service", "status": "active", "tags": ["customer-facing"]})
    save_component(d, {"id": "ledger", "name": "Ledger", "type": "module", "status": "deprecated", "tags": ["pci-scope"]})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_search_by_name(runner, test_dir):
    result = runner.invoke(cli, ["search", "Payment", "--root", str(test_dir)])
    assert "Payment Gateway" in result.output
    assert "Auth" not in result.output


def test_search_by_tag(runner, test_dir):
    result = runner.invoke(cli, ["search", "--tag", "pci-scope", "--root", str(test_dir)])
    assert "Payment Gateway" in result.output
    assert "Ledger" in result.output
    assert "Auth" not in result.output


def test_search_by_type(runner, test_dir):
    result = runner.invoke(cli, ["search", "--type", "service", "--root", str(test_dir)])
    assert "Payment Gateway" in result.output
    assert "Auth Service" in result.output
    assert "Ledger" not in result.output
```

- [ ] **Step 2: Implement search command**

```python
# pathfinder/cli/search_cmd.py
"""Search command."""

import click

from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("search")
@click.argument("query", required=False)
@click.option("--tag", default=None, help="Filter by tag")
@click.option("--type", "type_", default=None, help="Filter by type")
@click.option("--status", default=None, help="Filter by status")
@click.option("--root", default=None, help="Project root directory")
def search_cmd(query, tag, type_, status, root):
    """Search components by name, tag, or type."""
    project_root = resolve_root(root)
    index = build_index(project_root)

    results = list(index["components"].values())

    if query:
        q = query.lower()
        results = [c for c in results if q in c["name"].lower() or q in c["id"].lower()]

    if tag:
        results = [c for c in results if tag in c.get("tags", [])]

    if type_:
        results = [c for c in results if c["type"] == type_]

    if status:
        results = [c for c in results if c["status"] == status]

    if not results:
        click.echo("No components found")
        return

    click.echo(f"Found {len(results)} component(s):")
    for comp in results:
        tags = f" [{', '.join(comp.get('tags', []))}]" if comp.get("tags") else ""
        click.echo(f"  {comp['name']} ({comp['id']}) [{comp['type']}]{tags}")
```

- [ ] **Step 3: Wire into CLI and run tests**

Run: `pytest tests/cli/test_search.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add pathfinder/cli/search_cmd.py tests/cli/test_search.py pathfinder/cli/main.py
git commit -m "feat: CLI search command for querying by name, tag, type"
```

---

### Task 16: CLI — validate command

**Files:**
- Create: `pathfinder/cli/validate_cmd.py`
- Create: `tests/cli/test_validate.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/cli/test_validate.py
import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_no_issues_for_valid_graph(runner, test_dir):
    save_component(test_dir, {"id": "system", "name": "System", "type": "system", "status": "active"})
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "module", "status": "active", "parent": "system"})
    result = runner.invoke(cli, ["validate", "--root", str(test_dir)])
    assert "No issues" in result.output


def test_reports_broken_parent(runner, test_dir):
    save_component(test_dir, {"id": "orphan", "name": "Orphan", "type": "service", "status": "active", "parent": "nonexistent"})
    result = runner.invoke(cli, ["validate", "--root", str(test_dir)])
    assert "nonexistent" in result.output
    assert "does not exist" in result.output


def test_reports_broken_flow_target(runner, test_dir):
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "service", "status": "active",
                                "dataFlows": [{"to": "ghost", "data": "Something"}]})
    result = runner.invoke(cli, ["validate", "--root", str(test_dir)])
    assert "ghost" in result.output


def test_ci_exits_with_code_1(runner, test_dir):
    save_component(test_dir, {"id": "broken", "name": "Broken", "type": "service", "status": "active", "parent": "missing"})
    result = runner.invoke(cli, ["validate", "--ci", "--root", str(test_dir)])
    assert result.exit_code != 0
```

- [ ] **Step 2: Implement validate command**

```python
# pathfinder/cli/validate_cmd.py
"""Validate command — structural integrity."""

import sys

import click

from pathfinder.core.index_builder import validate_index
from pathfinder.cli.utils import resolve_root


@click.command("validate")
@click.option("--ci", is_flag=True, help="Exit with code 1 if issues found")
@click.option("--root", default=None, help="Project root directory")
def validate_cmd(ci: bool, root: str | None):
    """Check structural integrity of the component graph."""
    project_root = resolve_root(root)
    issues = validate_index(project_root)

    if not issues:
        click.echo("No issues found. Component graph is structurally valid.")
        return

    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    click.echo(f"Found {len(errors)} error(s) and {len(warnings)} warning(s):\n")
    for issue in issues:
        prefix = "ERROR" if issue["severity"] == "error" else "WARN"
        click.echo(f"  [{prefix}] {issue['component_id']}: {issue['issue']}")

    if ci and errors:
        sys.exit(1)
```

- [ ] **Step 3: Wire into CLI and run tests**

Run: `pytest tests/cli/test_validate.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add pathfinder/cli/validate_cmd.py tests/cli/test_validate.py pathfinder/cli/main.py
git commit -m "feat: CLI validate command for structural integrity"
```

---

### Task 17: Final CLI wiring + full test run

**Files:**
- Modify: `pathfinder/cli/main.py` (final version with all commands)

- [ ] **Step 1: Verify final main.py has all commands**

```python
# pathfinder/cli/main.py
"""Pathfinder CLI entry point."""

import click

from pathfinder.cli.init_cmd import init_cmd
from pathfinder.cli.add_cmd import add_cmd
from pathfinder.cli.set_cmd import set_cmd
from pathfinder.cli.remove_cmd import remove_cmd
from pathfinder.cli.move_cmd import move_cmd
from pathfinder.cli.list_cmd import list_cmd
from pathfinder.cli.info_cmd import info_cmd
from pathfinder.cli.show_cmd import show_cmd, children_cmd
from pathfinder.cli.search_cmd import search_cmd
from pathfinder.cli.deps_cmd import deps_cmd, dependents_cmd
from pathfinder.cli.flows_cmd import flows_cmd, trace_cmd, flow_add_cmd
from pathfinder.cli.map_cmd import map_cmd, mapped_cmd, unmapped_cmd
from pathfinder.cli.drift_cmd import drift_group
from pathfinder.cli.validate_cmd import validate_cmd
from pathfinder.cli.standards_cmd import standards_cmd
from pathfinder.cli.export_cmd import export_cmd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Architecture-first component library CLI."""
    pass


cli.add_command(init_cmd)
cli.add_command(add_cmd)
cli.add_command(set_cmd)
cli.add_command(remove_cmd)
cli.add_command(move_cmd)
cli.add_command(list_cmd)
cli.add_command(info_cmd)
cli.add_command(show_cmd)
cli.add_command(children_cmd)
cli.add_command(search_cmd)
cli.add_command(deps_cmd)
cli.add_command(dependents_cmd)
cli.add_command(flows_cmd)
cli.add_command(trace_cmd)
cli.add_command(flow_add_cmd)
cli.add_command(map_cmd)
cli.add_command(mapped_cmd)
cli.add_command(unmapped_cmd)
cli.add_command(drift_group)
cli.add_command(validate_cmd)
cli.add_command(standards_cmd)
cli.add_command(export_cmd)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 2: Run full test suite**

Run: `pytest -v`
Expected: All tests PASS

- [ ] **Step 3: Manual smoke test**

Run:
```bash
pathfinder init --name "Demo"
pathfinder add system "Demo System"
pathfinder add module "Payment" --parent demo-system
pathfinder add service "Gateway" --parent demo-system.payment
pathfinder set demo-system.payment --tag pci-scope
pathfinder list
pathfinder info
pathfinder show demo-system.payment
pathfinder search --tag pci-scope
pathfinder validate
pathfinder export --format dot
```

Expected: Tree shows hierarchy, info shows summary, search finds tagged components, validate reports clean, dot exports valid Graphviz

- [ ] **Step 4: Commit**

```bash
git add pathfinder/cli/main.py
git commit -m "feat: wire all CLI commands together"
```

---

### Task 18: Skills — pathfinder-discover, pathfinder-define, pathfinder-navigate

**Files:**
- Create: `skills/pathfinder-discover/SKILL.md`
- Create: `skills/pathfinder-define/SKILL.md`
- Create: `skills/pathfinder-navigate/SKILL.md`

Skills are markdown files — no language change needed. See the design spec for full skill content. Each skill references `pathfinder` CLI commands which are language-agnostic.

- [ ] **Step 1: Create pathfinder-discover skill**

Write the full SKILL.md as defined in the design spec (brownfield discovery workflow).

- [ ] **Step 2: Create pathfinder-define skill**

Write the full SKILL.md as defined in the design spec (architecture definition workflow).

- [ ] **Step 3: Create pathfinder-navigate skill**

Write the full SKILL.md as defined in the design spec (orientation workflow).

- [ ] **Step 4: Commit**

```bash
git add skills/
git commit -m "feat: skills - pathfinder-discover, pathfinder-define, pathfinder-navigate"
```

---

### Task 19: Skills — pathfinder-implement, pathfinder-check

**Files:**
- Create: `skills/pathfinder-implement/SKILL.md`
- Create: `skills/pathfinder-check/SKILL.md`

- [ ] **Step 1: Create pathfinder-implement skill**

Write the full SKILL.md as defined in the design spec (TDD implementation workflow).

- [ ] **Step 2: Create pathfinder-check skill**

Write the full SKILL.md as defined in the design spec (drift detection + impact analysis).

- [ ] **Step 3: Commit**

```bash
git add skills/
git commit -m "feat: skills - pathfinder-implement, pathfinder-check"
```

---

### Task 20: System Architect Agent

**Files:**
- Create: `agents/system-architect.md`

- [ ] **Step 1: Create the agent definition**

Write the full agent markdown as defined in the design spec (bridges business requirements to architectural decisions).

- [ ] **Step 2: Commit**

```bash
git add agents/
git commit -m "feat: system architect agent definition"
```

---

### Task 21: Final verification

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`
Expected: All tests PASS with 0 failures

- [ ] **Step 2: Build and verify package**

Run: `pip install -e .`
Expected: No errors, `pathfinder` command available

- [ ] **Step 3: Test the entry point**

Run: `pathfinder --help`
Expected: Shows all commands

- [ ] **Step 4: End-to-end smoke test**

Run:
```bash
cd /tmp && mkdir pathfinder-e2e && cd pathfinder-e2e
pathfinder init --name "E2E Test"
pathfinder add system "Platform"
pathfinder add module "Payment" --parent platform
pathfinder add service "Gateway" --parent platform.payment
pathfinder flow-add platform.payment platform --data "PaymentResult"
pathfinder list
pathfinder flows
pathfinder export --format dot
pathfinder drift check
pathfinder validate
```

Expected: All commands run without error

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: pathfinder v0.1.0 - architecture-first component library"
```
