"""Standards command."""

import click

from pathfinder.core.storage import load_standards
from pathfinder.cli.utils import resolve_root


@click.command("standards")
@click.option("--root", default=None, help="Project root directory")
def standards_cmd(root: str | None):
    """Show project architectural standards."""
    project_root = resolve_root(root)
    standards = load_standards(project_root)

    if not standards:
        click.echo("No standards defined. Create .pathfinder/standards.yaml to add them.")
        return

    click.echo("Architectural Standards:")
    if standards.get("spec"):
        click.echo(f"\n{standards['spec']}")
