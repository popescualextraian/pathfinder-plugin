"""Shared CLI utilities."""
from pathlib import Path
import os

import click


def resolve_root(root: str | None) -> Path:
    if root:
        return Path(root).resolve()
    env_root = os.environ.get("PATHFINDER_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd()


def resolve_index_id(index: dict, id_: str) -> str:
    """Resolve a component ID against the index, accepting slash or dot notation."""
    if id_ in index["components"]:
        return id_
    if "/" in id_:
        dot_id = id_.replace("/", ".")
        if dot_id in index["components"]:
            return dot_id
    raise click.ClickException(
        f"Component '{id_}' not found. Use 'pathfinder list' to see all components."
    )
