"""Remove command."""
import click
from pathfinder.core.storage import delete_component
from pathfinder.core.index_builder import build_index
from pathfinder.core.graph import get_dependents
from pathfinder.cli.utils import resolve_root, resolve_index_id

def collect_descendants(index: dict, comp_id: str) -> list[str]:
    result = [comp_id]
    entry = index["components"].get(comp_id)
    if entry:
        for child_id in entry.get("children", []):
            result.extend(collect_descendants(index, child_id))
    return result

@click.command("remove")
@click.argument("id_")
@click.option("--force", is_flag=True, help="Skip confirmation and remove")
@click.option("--dry-run", is_flag=True, help="Show what would be removed")
@click.option("--root", default=None, help="Project root directory")
def remove_cmd(id_: str, force: bool, dry_run: bool, root: str | None):
    """Remove a component and its children recursively."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    id_ = resolve_index_id(index, id_)
    entry = index["components"][id_]
    to_remove = collect_descendants(index, id_)
    external_dependents = []
    for remove_id in to_remove:
        for dep in get_dependents(index, remove_id):
            if dep not in to_remove and dep not in external_dependents:
                external_dependents.append(dep)
    if dry_run:
        click.echo(f"Would remove {len(to_remove)} component(s):")
        for r in to_remove:
            name = index["components"].get(r, {}).get("name", r)
            click.echo(f"  {name} ({r})")
        if external_dependents:
            click.echo("\nWarning: these components have flows referencing removed components:")
            for dep in external_dependents:
                name = index["components"].get(dep, {}).get("name", dep)
                click.echo(f"  {name} ({dep})")
        return
    if not force and (len(to_remove) > 1 or external_dependents):
        raise click.ClickException(
            f"Component '{id_}' has {len(to_remove) - 1} children and "
            f"{len(external_dependents)} external dependents. "
            f"Use --dry-run to see details, or --force to remove anyway.")
    for remove_id in reversed(to_remove):
        delete_component(project_root, remove_id)
    build_index(project_root)
    click.echo(f"Removed {len(to_remove)} component(s) starting from '{id_}'")
