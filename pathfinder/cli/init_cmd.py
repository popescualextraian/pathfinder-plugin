"""Init command."""
import click
from pathfinder.core.storage import init_project
from pathfinder.cli.utils import resolve_root

@click.command("init")
@click.option("--name", required=True, help="Project name")
@click.option("--root", default=None, help="Project root directory")
def init_cmd(name: str, root: str | None):
    """Initialize a new Pathfinder project."""
    project_root = resolve_root(root)
    try:
        init_project(project_root, name)
        click.echo(f"Initialized Pathfinder project '{name}' in {project_root}/.pathfinder/")
    except RuntimeError as e:
        raise click.ClickException(str(e))
