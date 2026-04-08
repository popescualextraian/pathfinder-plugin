"""List command — tree view."""
import click
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root

def print_tree(index, comp_id, prefix, is_last, max_level, current_level):
    entry = index["components"].get(comp_id)
    if not entry:
        return
    connector = "" if prefix == "" else ("└── " if is_last else "├── ")
    type_tag = f"[{entry['type']}]"
    status_tag = f" ({entry['status']})" if entry["status"] != "active" else ""
    click.echo(f"{prefix}{connector}{entry['name']} {type_tag}{status_tag}")
    if max_level > 0 and current_level >= max_level:
        return
    children = entry.get("children", [])
    child_prefix = "" if prefix == "" else prefix + ("    " if is_last else "│   ")
    for i, child_id in enumerate(children):
        print_tree(index, child_id, child_prefix, i == len(children) - 1, max_level, current_level + 1)

@click.command("list")
@click.option("--level", type=int, default=0, help="Maximum depth to show")
@click.option("--root", default=None, help="Project root directory")
def list_cmd(level: int, root: str | None):
    """Show component tree."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    roots = [c for c in index["components"].values() if not c.get("parent")]
    if not roots:
        click.echo("No components defined. Use 'pathfinder add' to create one.")
        return
    for i, root_comp in enumerate(roots):
        print_tree(index, root_comp["id"], "", i == len(roots) - 1, level, 0)
