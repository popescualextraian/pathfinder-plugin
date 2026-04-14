import subprocess
from pathlib import Path

import click
import yaml


def _container_status(name: str) -> str:
    """Get container status string."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Status}}", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "not found"
    return result.stdout.strip()


@click.command("info")
@click.option(
    "--root",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Project root directory. Defaults to current directory.",
)
def info_cmd(root):
    """Show Pathfinder project summary."""
    project_root = Path(root) if root else Path.cwd()
    pf_dir = project_root / ".pathfinder"

    if not pf_dir.exists():
        click.echo("No .pathfinder/ directory found. Run 'pathfinder init' first.")
        return

    # Read config
    config_file = pf_dir / "config.yaml"
    if config_file.exists():
        config = yaml.safe_load(config_file.read_text()) or {}
        click.echo(f"Project: {config.get('project_name', 'unknown')}")
    else:
        click.echo("Project: unknown (no config.yaml)")

    # Workspace status
    dsl_file = pf_dir / "workspace.dsl"
    if dsl_file.exists():
        size = dsl_file.stat().st_size
        click.echo(f"Workspace: {dsl_file.name} ({size} bytes)")
    else:
        click.echo("Workspace: not found")

    # Practices
    practices_file = pf_dir / "practices.md"
    click.echo(f"Practices: {'found' if practices_file.exists() else 'not found'}")

    # Docker containers
    click.echo()
    click.echo("Infrastructure:")
    click.echo(f"  Structurizr Server: {_container_status('pathfinder-server')}")
    click.echo(f"  MCP Server:         {_container_status('pathfinder-mcp')}")
