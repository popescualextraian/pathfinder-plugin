"""Install command — copy pathfinder skills and agent into a target project."""

import shutil
from pathlib import Path

import click

from pathfinder.cli.utils import resolve_root


def _package_data_dir() -> Path:
    """Return the directory containing bundled skills/agents inside the installed package."""
    return Path(__file__).resolve().parent.parent


@click.command("install")
@click.option("--root", default=None, help="Target project root directory")
@click.option("--skills-dir", default="skills", help="Destination directory for skills (default: skills/)")
@click.option("--agents-dir", default="agents", help="Destination directory for agents (default: agents/)")
def install_cmd(root: str | None, skills_dir: str, agents_dir: str):
    """Install pathfinder skills and agent into a project."""
    project_root = Path(resolve_root(root))
    pkg_dir = _package_data_dir()

    src_skills = pkg_dir / "skills"
    src_agents = pkg_dir / "agents"

    if not src_skills.exists():
        raise click.ClickException(
            f"Bundled skills not found at {src_skills}. "
            "Reinstall pathfinder: pip install pathfinder"
        )

    dest_skills = project_root / skills_dir
    dest_agents = project_root / agents_dir

    # Copy skills
    copied_skills = []
    for skill_src in sorted(src_skills.iterdir()):
        if not skill_src.is_dir():
            continue
        skill_dest = dest_skills / skill_src.name
        if skill_dest.exists():
            shutil.rmtree(skill_dest)
        shutil.copytree(skill_src, skill_dest)
        copied_skills.append(skill_src.name)

    # Copy agents
    copied_agents = []
    if src_agents.exists():
        dest_agents.mkdir(parents=True, exist_ok=True)
        for agent_src in sorted(src_agents.iterdir()):
            if not agent_src.is_file():
                continue
            agent_dest = dest_agents / agent_src.name
            shutil.copy2(agent_src, agent_dest)
            copied_agents.append(agent_src.name)

    # Report
    click.echo("Pathfinder installed successfully.\n")
    click.echo(f"Skills ({len(copied_skills)}):")
    for name in copied_skills:
        click.echo(f"  {dest_skills / name}/")
    if copied_agents:
        click.echo(f"\nAgents ({len(copied_agents)}):")
        for name in copied_agents:
            click.echo(f"  {dest_agents / name}")

    # CLAUDE.md guidance
    click.echo("\n--- Add to your project's CLAUDE.md ---\n")
    click.echo("## Pathfinder\n")
    click.echo("This project uses pathfinder for architecture-driven development.")
    click.echo("The `pathfinder` CLI must be installed and on PATH (`pip install pathfinder`).\n")
    click.echo("### Skills\n")
    click.echo(f"Skills are in `{skills_dir}/` — Claude Code will discover them automatically.")
    click.echo("- **pathfinder-discover** — onboard a codebase into pathfinder")
    click.echo("- **pathfinder-define** — decompose requirements into components and flows")
    click.echo("- **pathfinder-navigate** — load relevant architecture context for a task")
    click.echo("- **pathfinder-implement** — TDD implementation within component boundaries")
    click.echo("- **pathfinder-check** — architecture health checks and impact analysis\n")
    click.echo("### Agent\n")
    click.echo(f"The system architect agent is in `{agents_dir}/system-architect.md`.")
    click.echo("It bridges business requirements to component-scoped implementation tasks.")
