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
            "dependsOn": comp.get("dependsOn", []),
            "external": comp.get("external", False),
            "filePath": str(get_component_dir(project_root, comp_id) / "_component.yaml"),
        }

    for entry in entries.values():
        parent = entry.get("parent")
        if parent and parent in entries:
            entries[parent]["children"].append(entry["id"])

    flows: list[dict] = []
    for comp in components:
        for flow in comp.get("dataFlows", []):
            flows.append({
                "from": flow.get("from", comp["id"]),
                "to": flow.get("to"),
                "data": flow["data"],
                "protocol": flow.get("protocol"),
                "pattern": flow.get("pattern"),
            })

    index = {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "components": entries,
        "flows": flows,
    }

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
        parent = comp.get("parent")
        if parent and parent not in index["components"]:
            issues.append({
                "component_id": comp["id"],
                "issue": f"Parent '{parent}' does not exist",
                "severity": "error",
            })

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

        for dep_id in comp.get("dependsOn", []):
            if dep_id not in index["components"]:
                issues.append({
                    "component_id": comp["id"],
                    "issue": f"dependsOn references unknown component '{dep_id}'",
                    "severity": "error",
                })

        expected_dir = get_component_dir(project_root, comp["id"])
        actual_dir = Path(comp["filePath"]).parent
        if expected_dir.resolve() != actual_dir.resolve():
            issues.append({
                "component_id": comp["id"],
                "issue": f"ID '{comp['id']}' does not match folder path",
                "severity": "error",
            })

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
