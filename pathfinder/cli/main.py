"""Pathfinder CLI entry point."""

import click
from pathfinder.cli.init_cmd import init_cmd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Architecture-first component library CLI."""
    pass

cli.add_command(init_cmd)

if __name__ == "__main__":
    cli()
