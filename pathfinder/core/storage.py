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
