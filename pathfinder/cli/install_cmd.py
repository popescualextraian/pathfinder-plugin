import json
import shutil
from pathlib import Path

import click


def _package_dir() -> Path:
    """Return the pathfinder package directory (where skills/ and agents/ live)."""
    return Path(__file__).resolve().parent.parent


MCP_CONFIG = {
    "structurizr": {
        "type": "sse",
        "url": "http://localhost:3000/mcp",
    }
}


@click.command("install")
@click.option(
    "--root",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Project root directory. Defaults to current directory.",
)
def install_cmd(root):
    """Install Pathfinder skills, agents, and MCP config into the target project."""
    project_root = Path(root) if root else Path.cwd()
    pkg_dir = _package_dir()
    claude_dir = project_root / ".claude"

    # --- Skills ---
    skills_src = pkg_dir / "skills"
    skills_dst = claude_dir / "skills"
    skill_count = 0

    if skills_src.exists():
        for skill_dir in sorted(skills_src.iterdir()):
            if skill_dir.is_dir():
                dst = skills_dst / skill_dir.name
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(skill_dir, dst)
                skill_count += 1

    # --- Agents ---
    agents_src = pkg_dir / "agents"
    agents_dst = claude_dir / "agents"
    agent_count = 0

    if agents_src.exists():
        agents_dst.mkdir(parents=True, exist_ok=True)
        for agent_file in sorted(agents_src.iterdir()):
            if agent_file.is_file() and agent_file.suffix == ".md":
                dst = agents_dst / agent_file.name
                shutil.copy2(agent_file, dst)
                agent_count += 1

    # --- MCP Server Config ---
    settings_file = claude_dir / "settings.local.json"
    settings = {}
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except (json.JSONDecodeError, OSError):
            settings = {}

    mcp_servers = settings.get("mcpServers", {})
    mcp_servers.update(MCP_CONFIG)
    settings["mcpServers"] = mcp_servers

    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(settings, indent=2) + "\n")

    click.echo(f"Installed into {claude_dir}:")
    click.echo(f"  {skill_count} skills")
    click.echo(f"  {agent_count} agents")
    click.echo(f"  MCP server config (Structurizr at localhost:3000)")
    click.echo()
    click.echo("Next steps:")
    click.echo("  pathfinder init --name <project>   # If not done already")
    click.echo("  pathfinder start                    # Start Docker containers")
