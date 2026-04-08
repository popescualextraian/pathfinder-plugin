"""Graph operations: deps, dependents, trace, flow queries."""
from __future__ import annotations
from collections import deque
from fnmatch import fnmatch

def get_dependencies(index: dict, component_id: str) -> list[str]:
    deps = set()
    for flow in index["flows"]:
        if flow.get("from") == component_id and flow.get("to"):
            deps.add(flow["to"])
    return list(deps)

def get_dependents(index: dict, component_id: str) -> list[str]:
    dependents = set()
    for flow in index["flows"]:
        if flow.get("to") == component_id and flow.get("from"):
            dependents.add(flow["from"])
    return list(dependents)

def get_flows_for_component(index: dict, component_id: str) -> list[dict]:
    return [f for f in index["flows"] if f.get("from") == component_id or f.get("to") == component_id]

def trace_flow(index: dict, from_id: str, to_id: str) -> list[str] | None:
    if from_id == to_id:
        return [from_id]
    adj: dict[str, set[str]] = {}
    for flow in index["flows"]:
        src, dst = flow.get("from"), flow.get("to")
        if src and dst:
            adj.setdefault(src, set()).add(dst)
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
    return [c["id"] for c in index["components"].values() if tag in c.get("tags", [])]

def find_component_by_code_path(index: dict, file_path: str) -> str | None:
    best_match, best_specificity = None, 0
    for comp in index["components"].values():
        for mapping in comp.get("codeMappings", []):
            if fnmatch(file_path, mapping["glob"]):
                specificity = len(mapping["glob"])
                if specificity > best_specificity:
                    best_specificity = specificity
                    best_match = comp["id"]
    return best_match
