"""Map commands — map, mapped, unmapped."""

import click

from pathfinder.core.storage import load_component, save_component
from pathfinder.core.index_builder import build_index
from pathfinder.core.graph import find_component_by_code_path
from pathfinder.cli.utils import resolve_root


@click.command("map")
@click.argument("id_")
@click.option("--glob", "glob_pattern", required=True, help="Glob pattern for files")
@click.option("--repo", default=None, help="Repository name")
@click.option("--root", default=None, help="Project root directory")
def map_cmd(id_, glob_pattern, repo, root):
    """Map code files to a component."""
    project_root = resolve_root(root)
    component = load_component(project_root, id_)
    mappings = component.get("codeMappings", [])
    new_mapping = {"glob": glob_pattern}
    if repo:
        new_mapping["repo"] = repo
    mappings.append(new_mapping)
    component["codeMappings"] = mappings
    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Mapped {glob_pattern} \u2192 {component['name']} ({id_})")


@click.command("mapped")
@click.argument("file")
@click.option("--root", default=None, help="Project root directory")
def mapped_cmd(file, root):
    """Find which component owns a file."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    comp_id = find_component_by_code_path(index, file)
    if comp_id:
        comp = index["components"][comp_id]
        click.echo(f"{file} \u2192 {comp['name']} ({comp_id})")
    else:
        click.echo(f"No component mapped to {file}")


@click.command("unmapped")
@click.option("--root", default=None, help="Project root directory")
def unmapped_cmd(root):
    """List components with no code mappings."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    unmapped = [c for c in index["components"].values() if not c.get("codeMappings")]
    if not unmapped:
        click.echo("All components have code mappings")
        return
    click.echo(f"Components without code mappings ({len(unmapped)}):")
    for comp in unmapped:
        click.echo(f"  {comp['name']} ({comp['id']}) [{comp['type']}]")
