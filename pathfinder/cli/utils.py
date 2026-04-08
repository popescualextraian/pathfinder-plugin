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
