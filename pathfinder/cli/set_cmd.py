"""Set command — update component fields."""

import click
from pathlib import Path

from pathfinder.core.storage import load_component, save_component, resolve_component_id
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("set")
@click.argument("id_")
@click.option("--status", default=None, help="Set status (proposed, active, deprecated)")
@click.option("--type", "type_", default=None, help="Set type")
@click.option("--tag", default=None, help="Add a tag")
@click.option("--remove-tag", default=None, help="Remove a tag")
@click.option("--spec", default=None, help="Set spec text")
@click.option("--spec-file", default=None, type=click.Path(exists=True), help="Set spec from file")
@click.option("--root", default=None, help="Project root directory")
def set_cmd(id_: str, status, type_, tag, remove_tag, spec, spec_file, root):
    """Update component fields."""
    project_root = resolve_root(root)
    id_ = resolve_component_id(project_root, id_)
    component = load_component(project_root, id_)
    changes = []

    if status:
        component["status"] = status
        changes.append(f"status -> {status}")

    if type_:
        component["type"] = type_
        changes.append(f"type -> {type_}")

    if tag:
        tags = component.get("tags", [])
        if tag not in tags:
            tags.append(tag)
            component["tags"] = tags
            changes.append(f"+tag {tag}")

    if remove_tag:
        tags = component.get("tags", [])
        if remove_tag in tags:
            tags.remove(remove_tag)
            component["tags"] = tags
            changes.append(f"-tag {remove_tag}")

    if spec:
        component["spec"] = spec
        changes.append("spec updated")

    if spec_file:
        component["spec"] = Path(spec_file).read_text()
        changes.append(f"spec loaded from {spec_file}")

    if not changes:
        click.echo("No changes specified")
        return

    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Updated {component['name']} ({id_}): {', '.join(changes)}")
