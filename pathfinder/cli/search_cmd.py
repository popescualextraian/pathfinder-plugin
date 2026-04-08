"""Search command."""

import click

from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("search")
@click.argument("query", required=False)
@click.option("--tag", default=None, help="Filter by tag")
@click.option("--type", "type_", default=None, help="Filter by type")
@click.option("--status", default=None, help="Filter by status")
@click.option("--root", default=None, help="Project root directory")
def search_cmd(query, tag, type_, status, root):
    """Search components by name, tag, or type."""
    project_root = resolve_root(root)
    index = build_index(project_root)

    results = list(index["components"].values())

    if query:
        q = query.lower()
        results = [c for c in results if q in c["name"].lower() or q in c["id"].lower()]

    if tag:
        results = [c for c in results if tag in c.get("tags", [])]

    if type_:
        results = [c for c in results if c["type"] == type_]

    if status:
        results = [c for c in results if c["status"] == status]

    if not results:
        click.echo("No components found")
        return

    click.echo(f"Found {len(results)} component(s):")
    for comp in results:
        tags = f" [{', '.join(comp.get('tags', []))}]" if comp.get("tags") else ""
        click.echo(f"  {comp['name']} ({comp['id']}) [{comp['type']}]{tags}")
