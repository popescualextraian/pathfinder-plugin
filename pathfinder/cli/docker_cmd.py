import subprocess
from pathlib import Path

import click


SERVER_CONTAINER = "pathfinder-server"
MCP_CONTAINER = "pathfinder-mcp"
SERVER_IMAGE = "structurizr/structurizr"
MCP_IMAGE = "structurizr/mcp"


def _container_running(name: str) -> bool:
    """Check if a Docker container is running."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}", name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _container_exists(name: str) -> bool:
    """Check if a Docker container exists (running or stopped)."""
    result = subprocess.run(
        ["docker", "inspect", name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _start_container(name: str, args: list[str]) -> bool:
    """Start a Docker container. Returns True on success."""
    if _container_running(name):
        click.echo(f"  {name} already running")
        return True

    if _container_exists(name):
        result = subprocess.run(
            ["docker", "start", name],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.echo(f"  {name} started (existing container)")
            return True
        click.echo(f"  Error starting {name}: {result.stderr.strip()}", err=True)
        return False

    result = subprocess.run(
        ["docker", "run", "-d", "--name", name] + args,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        click.echo(f"  {name} started")
        return True
    click.echo(f"  Error creating {name}: {result.stderr.strip()}", err=True)
    return False


def _stop_container(name: str) -> bool:
    """Stop a Docker container. Returns True on success."""
    if not _container_exists(name):
        click.echo(f"  {name} not found")
        return True

    if not _container_running(name):
        click.echo(f"  {name} already stopped")
        return True

    result = subprocess.run(
        ["docker", "stop", name],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        click.echo(f"  {name} stopped")
        return True
    click.echo(f"  Error stopping {name}: {result.stderr.strip()}", err=True)
    return False


@click.command("start")
@click.option("--port", default=8080, type=int, help="Port for Structurizr Server UI.")
@click.option(
    "--root",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Project root directory. Defaults to current directory.",
)
def start_cmd(port, root):
    """Start Structurizr Server and MCP Docker containers."""
    project_root = Path(root) if root else Path.cwd()
    pf_dir = project_root / ".pathfinder"

    if not pf_dir.exists():
        click.echo("Error: .pathfinder/ not found. Run 'pathfinder init' first.", err=True)
        raise SystemExit(1)

    # Check Docker is available
    result = subprocess.run(["docker", "info"], capture_output=True, text=True)
    if result.returncode != 0:
        click.echo("Error: Docker is not running or not installed.", err=True)
        raise SystemExit(1)

    click.echo("Starting Pathfinder infrastructure...")

    # Structurizr Server
    pf_abs = str(pf_dir.resolve()).replace("\\", "/")
    server_ok = _start_container(SERVER_CONTAINER, [
        "-p", f"{port}:8080",
        "-v", f"{pf_abs}:/usr/local/structurizr",
        SERVER_IMAGE, "server",
    ])

    # MCP Server
    mcp_ok = _start_container(MCP_CONTAINER, [
        "-p", "3000:3000",
        MCP_IMAGE,
        "-dsl", "-mermaid", "-plantuml",
        "-server-create", "-server-read", "-server-update", "-server-delete",
    ])

    if server_ok and mcp_ok:
        click.echo()
        click.echo(f"Structurizr Server: http://localhost:{port}")
        click.echo(f"MCP Server:         http://localhost:3000/mcp")
    else:
        click.echo()
        click.echo("Some containers failed to start. Check Docker logs.", err=True)
        raise SystemExit(1)


@click.command("stop")
def stop_cmd():
    """Stop Structurizr Server and MCP Docker containers."""
    click.echo("Stopping Pathfinder infrastructure...")
    _stop_container(MCP_CONTAINER)
    _stop_container(SERVER_CONTAINER)
    click.echo("Done.")
