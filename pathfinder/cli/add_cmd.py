"""Add command."""
import re
import click
from pathfinder.core.storage import save_component, load_component, load_config, save_config
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


def name_to_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@click.command("add")
@click.argument("type_", metavar="TYPE")
@click.argument("name")
@click.option("--parent", default=None, help="Parent component ID")
@click.option("--external", is_flag=True, help="Mark as external component")
@click.option("--spec", default=None, help="Set component spec/description")
@click.option("--root", default=None, help="Project root directory")
def add_cmd(type_: str, name: str, parent: str | None, external: bool, spec: str | None, root: str | None):
    """Add a new component."""
    project_root = resolve_root(root)

    config = load_config(project_root)
    known_types = config.get("componentTypes", [])
    if known_types and type_ not in known_types:
        if not click.confirm(f"Type '{type_}' is not in known types. Add it?"):
            raise click.ClickException(f"Aborted. Known types: {', '.join(known_types)}")
        known_types.append(type_)
        config["componentTypes"] = known_types
        save_config(project_root, config)

    slug = name_to_slug(name)
    comp_id = f"{parent}.{slug}" if parent else slug
    if parent:
        try:
            load_component(project_root, parent)
        except FileNotFoundError:
            raise click.ClickException(f"Parent component '{parent}' not found")
    comp = {"id": comp_id, "name": name, "type": type_, "status": "active", "parent": parent}
    if external:
        comp["external"] = True
    if spec:
        comp["spec"] = spec
    save_component(project_root, comp)
    build_index(project_root)
    click.echo(f"Added {type_} '{name}' ({comp_id})")
