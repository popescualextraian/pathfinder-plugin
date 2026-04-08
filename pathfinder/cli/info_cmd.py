"""Info command — project summary."""

import click

from pathfinder.core.storage import load_config
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("info")
@click.option("--root", default=None, help="Project root directory")
def info_cmd(root: str | None):
    """Show project summary."""
    project_root = resolve_root(root)
    config = load_config(project_root)
    index = build_index(project_root)

    components = list(index["components"].values())
    by_type: dict[str, int] = {}
    tags: set[str] = set()

    for comp in components:
        by_type[comp["type"]] = by_type.get(comp["type"], 0) + 1
        for t in comp.get("tags", []):
            tags.add(t)

    click.echo(f"Project: {config['name']}")
    click.echo(f"Components: {len(components)}")
    click.echo(f"Data flows: {len(index['flows'])}")

    if by_type:
        click.echo("\nBy type:")
        for type_, count in by_type.items():
            click.echo(f"  {type_}: {count}")

    if tags:
        click.echo(f"\nTags: {', '.join(sorted(tags))}")

    repos = config.get("repos", {})
    if repos:
        click.echo(f"\nRepos: {', '.join(repos.keys())}")
