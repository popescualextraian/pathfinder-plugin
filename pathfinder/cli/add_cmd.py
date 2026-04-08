"""Add command."""
import re
import click
from pathfinder.core.storage import save_component, load_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root

def name_to_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

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
    save_component(project_root, {"id": comp_id, "name": name, "type": type_, "status": "active", "parent": parent})
    build_index(project_root)
    click.echo(f"Added {type_} '{name}' ({comp_id})")
