"""Move command."""
import click
from pathfinder.core.storage import load_component, save_component, delete_component, resolve_component_id
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root

@click.command("move")
@click.argument("id_")
@click.option("--parent", required=True, help="New parent component ID")
@click.option("--root", default=None, help="Project root directory")
def move_cmd(id_: str, parent: str, root: str | None):
    """Move a component to a new parent."""
    project_root = resolve_root(root)
    id_ = resolve_component_id(project_root, id_)
    component = load_component(project_root, id_)
    try:
        parent = resolve_component_id(project_root, parent)
    except FileNotFoundError:
        raise click.ClickException(f"Parent component '{parent}' not found")
    slug = id_.rsplit(".", 1)[-1] if "." in id_ else id_
    new_id = f"{parent}.{slug}"
    delete_component(project_root, id_)
    component["id"] = new_id
    component["parent"] = parent
    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Moved '{id_}' -> '{new_id}' (parent: {parent})")
