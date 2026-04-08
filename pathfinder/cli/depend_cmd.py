"""Depend command — manage structural dependencies."""

import click

from pathfinder.core.storage import load_component, save_component
from pathfinder.core.index_builder import build_index
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
