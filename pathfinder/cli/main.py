"""Pathfinder CLI entry point."""

import click

from pathfinder.cli.init_cmd import init_cmd
from pathfinder.cli.add_cmd import add_cmd
from pathfinder.cli.set_cmd import set_cmd
from pathfinder.cli.remove_cmd import remove_cmd
from pathfinder.cli.move_cmd import move_cmd
from pathfinder.cli.list_cmd import list_cmd
from pathfinder.cli.info_cmd import info_cmd
from pathfinder.cli.show_cmd import show_cmd, children_cmd
from pathfinder.cli.search_cmd import search_cmd
from pathfinder.cli.deps_cmd import deps_cmd, dependents_cmd
from pathfinder.cli.flows_cmd import flows_cmd, trace_cmd, flow_add_cmd
from pathfinder.cli.map_cmd import map_cmd, mapped_cmd, unmapped_cmd
from pathfinder.cli.drift_cmd import drift_group
from pathfinder.cli.validate_cmd import validate_cmd
from pathfinder.cli.standards_cmd import standards_cmd
from pathfinder.cli.export_cmd import export_cmd
from pathfinder.cli.depend_cmd import depend_cmd
from pathfinder.cli.contract_cmd import contract_add_cmd, contract_remove_cmd
from pathfinder.cli.install_cmd import install_cmd
from pathfinder.cli.help_cmd import help_cmd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Pathfinder Plugin — architecture-first skills and agent for AI-driven development."""
    pass


cli.add_command(init_cmd)
cli.add_command(add_cmd)
cli.add_command(set_cmd)
cli.add_command(remove_cmd)
cli.add_command(move_cmd)
cli.add_command(list_cmd)
cli.add_command(info_cmd)
cli.add_command(show_cmd)
cli.add_command(children_cmd)
cli.add_command(search_cmd)
cli.add_command(deps_cmd)
cli.add_command(dependents_cmd)
cli.add_command(flows_cmd)
cli.add_command(trace_cmd)
cli.add_command(flow_add_cmd)
cli.add_command(map_cmd)
cli.add_command(mapped_cmd)
cli.add_command(unmapped_cmd)
cli.add_command(drift_group)
cli.add_command(validate_cmd)
cli.add_command(standards_cmd)
cli.add_command(export_cmd)
cli.add_command(depend_cmd)
cli.add_command(contract_add_cmd)
cli.add_command(contract_remove_cmd)
cli.add_command(install_cmd)
cli.add_command(help_cmd)


if __name__ == "__main__":
    cli()
