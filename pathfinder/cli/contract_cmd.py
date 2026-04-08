"""Contract commands — contract-add, contract-remove."""

import click

from pathfinder.core.storage import load_component, save_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root


@click.command("contract-add")
@click.argument("id_")
@click.option("--input", "is_input", is_flag=True, help="Add as input contract")
@click.option("--output", "is_output", is_flag=True, help="Add as output contract")
@click.option("--name", required=True, help="Contract name")
@click.option("--format", "fmt", required=True, help="Contract format description")
@click.option("--version", default=None, help="Contract version")
@click.option("--source", default=None, help="Source component (for inputs)")
@click.option("--target", default=None, help="Target component (for outputs)")
@click.option("--root", default=None, help="Project root directory")
def contract_add_cmd(id_: str, is_input: bool, is_output: bool, name: str, fmt: str,
                     version: str | None, source: str | None, target: str | None, root: str | None):
    """Add a contract to a component."""
    if not is_input and not is_output:
        raise click.ClickException("Specify --input or --output")

    project_root = resolve_root(root)
    component = load_component(project_root, id_)
    contracts = component.get("contracts", {"inputs": [], "outputs": []})
    if "inputs" not in contracts:
        contracts["inputs"] = []
    if "outputs" not in contracts:
        contracts["outputs"] = []

    contract = {"name": name, "format": fmt}
    if version:
        contract["version"] = version

    if is_input:
        if source:
            contract["source"] = source
        contracts["inputs"].append(contract)
        direction = "input"
    else:
        if target:
            contract["target"] = target
        contracts["outputs"].append(contract)
        direction = "output"

    component["contracts"] = contracts
    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Added {direction} contract '{name}' to {component['name']} ({id_})")


@click.command("contract-remove")
@click.argument("id_")
@click.option("--name", required=True, help="Contract name to remove")
@click.option("--root", default=None, help="Project root directory")
def contract_remove_cmd(id_: str, name: str, root: str | None):
    """Remove a contract from a component."""
    project_root = resolve_root(root)
    component = load_component(project_root, id_)
    contracts = component.get("contracts", {"inputs": [], "outputs": []})

    found = False
    for direction in ("inputs", "outputs"):
        original = contracts.get(direction, [])
        filtered = [c for c in original if c["name"] != name]
        if len(filtered) < len(original):
            found = True
            contracts[direction] = filtered

    if not found:
        raise click.ClickException(f"Contract '{name}' not found on {id_}")

    component["contracts"] = contracts
    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Removed contract '{name}' from {component['name']} ({id_})")
