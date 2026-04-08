"""Pathfinder CLI entry point."""

import click


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Architecture-first component library CLI."""
    pass


if __name__ == "__main__":
    cli()
