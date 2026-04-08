"""Pathfinder CLI entry point."""

import click
from pathfinder.cli.init_cmd import init_cmd
from pathfinder.cli.add_cmd import add_cmd
from pathfinder.cli.remove_cmd import remove_cmd
from pathfinder.cli.move_cmd import move_cmd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Architecture-first component library CLI."""
    pass

cli.add_command(init_cmd)
cli.add_command(add_cmd)
cli.add_command(remove_cmd)
cli.add_command(move_cmd)

if __name__ == "__main__":
    cli()
