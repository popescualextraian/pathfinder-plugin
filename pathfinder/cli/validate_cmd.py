"""Validate command — structural integrity."""

import sys

import click

from pathfinder.core.index_builder import validate_index
from pathfinder.cli.utils import resolve_root


@click.command("validate")
@click.option("--ci", is_flag=True, help="Exit with code 1 if issues found")
@click.option("--root", default=None, help="Project root directory")
def validate_cmd(ci: bool, root: str | None):
    """Check structural integrity of the component graph."""
    project_root = resolve_root(root)
    issues = validate_index(project_root)

    if not issues:
        click.echo("No issues found. Component graph is structurally valid.")
        return

    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    click.echo(f"Found {len(errors)} error(s) and {len(warnings)} warning(s):\n")
    for issue in issues:
        prefix = "ERROR" if issue["severity"] == "error" else "WARN"
        click.echo(f"  [{prefix}] {issue['component_id']}: {issue['issue']}")

    if ci and errors:
        sys.exit(1)
