import click

from pathfinder.cli.init_cmd import init_cmd
from pathfinder.cli.install_cmd import install_cmd
from pathfinder.cli.docker_cmd import start_cmd, stop_cmd
from pathfinder.cli.info_cmd import info_cmd


@click.group()
@click.version_option(version="0.2.0", prog_name="pathfinder")
def cli():
    """Pathfinder — AI-driven architecture management using Structurizr and C4."""
    pass


cli.add_command(init_cmd, "init")
cli.add_command(install_cmd, "install")
cli.add_command(start_cmd, "start")
cli.add_command(stop_cmd, "stop")
cli.add_command(info_cmd, "info")


if __name__ == "__main__":
    cli()
