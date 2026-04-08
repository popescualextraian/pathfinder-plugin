# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
pip install -e ".[dev]"        # Install in dev mode with pytest
pytest tests/                  # Run all tests
pytest tests/cli/test_add.py   # Run a single test file
pytest tests/ -v --tb=short    # Verbose with short tracebacks
```

Entry point: `pathfinder = "pathfinder.cli.main:cli"` (Click CLI, Python >=3.12).
Dependencies: click>=8.1, pyyaml>=6.0. Dev: pytest>=8.0. Build: hatchling.

## Architecture

Pathfinder is an **architecture-first component library CLI** that models applications as hierarchical DAGs with explicit data flows. Components are the unit of work, not tasks or stories.

### Three-layer design

1. **`pathfinder/core/`** — Business logic, no CLI awareness
   - `storage.py` — YAML file I/O. Component IDs use dot notation (`payment.gateway`) mapped to paths (`payment/gateway/_component.yaml`).
   - `index_builder.py` — Builds `index.json` (flat graph) from YAML files. Lazy rebuild: stale-checked on reads, always rebuilt on writes.
   - `graph.py` — Graph queries on the index: deps, dependents, flows, BFS trace, tag queries, code path matching (glob specificity ranking).

2. **`pathfinder/cli/`** — Click commands, one file per command (21 commands registered in `main.py`)
   - Each command resolves project root via `utils.resolve_root()` (`--root` flag > `PATHFINDER_ROOT` env > cwd).
   - Mutations call core functions then `build_index()`. Reads call `ensure_index()`.
   - Errors: `click.ClickException` for user-facing; `FileNotFoundError` from storage layer.

3. **`pathfinder/types.py`** — Shared dataclasses (`Component`, `DataFlow`, `CodeMapping`, `Contracts`, etc.). No external imports.

### Data model

- **Component** — A node with `id` (dot-notation), `type` (hint, not constraint), `status`, `parent`, `spec` (free-form), `contracts` (free-form), `data_flows`, `code_mappings`, `tags`.
- **Index** (`index.json`) — Generated flat graph: `components` dict + `flows` list. Always derived from YAML source of truth.
- **Storage** (`.pathfinder/`) — `config.yaml`, `standards.yaml`, `components/` (hierarchical YAML), `index.json` (generated).

### Key design decisions

- `spec` and `contracts` are free-form text for LLM interpretation, not rigid schemas.
- `code_mappings` support multiple repos (one component can span Terraform + Lambda).
- `tags` handle cross-cutting concerns (e.g., query all `pci-scope` components).
- Hierarchy is structural; `type` is advisory.

## CLI Command Pattern

Every command follows this pattern:
```python
@click.command("name")
@click.argument("arg")
@click.option("--root", default=None)
def name_cmd(arg, root):
    project_root = resolve_root(root)
    # call core functions
    # rebuild index if mutating
    click.echo(result)
```

## Test Pattern

CLI tests use Click's `CliRunner` with a `tmp_path` fixture for isolated `.pathfinder/` directories. Core tests build minimal component graphs in-memory.

## Skills & Agents

- `skills/` — Five Claude Code skills (discover, define, navigate, implement, check) that drive AI-assisted architectural workflows.
- `agents/system-architect.md` — Architect agent that bridges business requirements to component-scoped implementation tasks. Does not write code.
