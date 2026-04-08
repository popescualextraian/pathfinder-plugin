"""Export command — json, dot, markdown."""

import json

import click

from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("export")
@click.option("--format", "fmt", required=True, type=click.Choice(["json", "dot", "markdown"]), help="Export format")
@click.option("--root", default=None, help="Project root directory")
def export_cmd(fmt: str, root: str | None):
    """Export component graph."""
    project_root = resolve_root(root)
    index = build_index(project_root)

    if fmt == "json":
        click.echo(json.dumps(index, indent=2))
    elif fmt == "dot":
        _export_dot(index)
    elif fmt == "markdown":
        _export_markdown(index)


def _export_dot(index):
    click.echo("digraph pathfinder {")
    click.echo("  rankdir=TB;")
    click.echo("  node [shape=box];")
    for comp in index["components"].values():
        label = f"{comp['name']}\\n[{comp['type']}]"
        click.echo(f'  "{comp["id"]}" [label="{label}"];')
    for comp in index["components"].values():
        for child_id in comp.get("children", []):
            click.echo(f'  "{comp["id"]}" -> "{child_id}" [style=dashed];')
    for flow in index["flows"]:
        label = flow["data"]
        click.echo(f'  "{flow["from"]}" -> "{flow["to"]}" [label="{label}"];')
    click.echo("}")


def _export_markdown(index):
    def _print_comp(comp_id, depth=0):
        comp = index["components"].get(comp_id)
        if not comp:
            return
        prefix = "#" * (depth + 1)
        click.echo(f"{prefix} {comp['name']} [{comp['type']}]")
        click.echo(f"\n**ID:** {comp['id']}  ")
        click.echo(f"**Status:** {comp['status']}  ")
        if comp.get("tags"):
            click.echo(f"**Tags:** {', '.join(comp['tags'])}  ")
        click.echo("")
        for child_id in comp.get("children", []):
            _print_comp(child_id, depth + 1)

    roots = [c for c in index["components"].values() if not c.get("parent")]
    for root_comp in roots:
        _print_comp(root_comp["id"])
