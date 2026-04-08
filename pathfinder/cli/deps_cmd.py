"""Deps and dependents commands."""
import click
from pathfinder.core.index_builder import build_index
from pathfinder.core.graph import get_dependencies, get_dependents
from pathfinder.cli.utils import resolve_root, resolve_index_id

@click.command("deps")
@click.argument("id_")
@click.option("--root", default=None, help="Project root directory")
def deps_cmd(id_: str, root: str | None):
    """Show what a component depends on."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    id_ = resolve_index_id(index, id_)
    deps = get_dependencies(index, id_)
    if not deps:
        click.echo(f"{index['components'][id_]['name']} has no dependencies")
        return
    click.echo(f"{index['components'][id_]['name']} depends on:")
    for dep_id in deps:
        dep = index["components"].get(dep_id)
        click.echo(f"  {dep['name'] if dep else dep_id} ({dep_id})")

@click.command("dependents")
@click.argument("id_")
@click.option("--root", default=None, help="Project root directory")
def dependents_cmd(id_: str, root: str | None):
    """Show what depends on a component."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    id_ = resolve_index_id(index, id_)
    deps = get_dependents(index, id_)
    if not deps:
        click.echo(f"Nothing depends on {index['components'][id_]['name']}")
        return
    click.echo(f"Components that depend on {index['components'][id_]['name']}:")
    for dep_id in deps:
        dep = index["components"].get(dep_id)
        click.echo(f"  {dep['name'] if dep else dep_id} ({dep_id})")
