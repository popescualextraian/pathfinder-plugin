"""Show and children commands."""
import click
from pathfinder.core.storage import load_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.utils import resolve_root

@click.command("show")
@click.argument("id_")
@click.option("--contracts", is_flag=True, help="Show only contracts")
@click.option("--root", default=None, help="Project root directory")
def show_cmd(id_: str, contracts: bool, root: str | None):
    """Show component details."""
    project_root = resolve_root(root)
    component = load_component(project_root, id_)
    if contracts:
        click.echo(f"Contracts for {component['name']} ({component['id']}):")
        c = component.get("contracts", {})
        for inp in c.get("inputs", []):
            source = f" (from: {inp['source']})" if inp.get("source") else ""
            version = f" v{inp['version']}" if inp.get("version") else ""
            click.echo(f"\n  Input: {inp['name']}{source}{version}")
            click.echo(f"    {inp['format'].strip()}")
        for out in c.get("outputs", []):
            target = f" (to: {out['target']})" if out.get("target") else ""
            version = f" v{out['version']}" if out.get("version") else ""
            click.echo(f"\n  Output: {out['name']}{target}{version}")
            click.echo(f"    {out['format'].strip()}")
        return
    click.echo(f"{component['name']} [{component['type']}] ({component['status']})")
    click.echo(f"ID: {component['id']}")
    if component.get("parent"):
        click.echo(f"Parent: {component['parent']}")
    if component.get("external"):
        click.echo("External: yes")
    if component.get("dependsOn"):
        click.echo(f"Depends on: {', '.join(component['dependsOn'])}")
    if component.get("tags"):
        click.echo(f"Tags: {', '.join(component['tags'])}")
    if component.get("spec"):
        lines = component["spec"].strip().split("\n")
        click.echo(f"\nSpec:\n  " + "\n  ".join(lines))
    c = component.get("contracts", {})
    for inp in c.get("inputs", []):
        click.echo(f"\nContract (input): {inp['name']}")
    for out in c.get("outputs", []):
        click.echo(f"\nContract (output): {out['name']}")
    for flow in component.get("dataFlows", []):
        direction = f"→ {flow['to']}" if flow.get("to") else f"← {flow.get('from')}"
        protocol = f" [{flow['protocol']}]" if flow.get("protocol") else ""
        click.echo(f"\nFlow: {direction}: {flow['data']}{protocol}")
    for mapping in component.get("codeMappings", []):
        repo = f"{mapping['repo']}:" if mapping.get("repo") else ""
        click.echo(f"\nCode: {repo}{mapping['glob']}")

@click.command("children")
@click.argument("id_")
@click.option("--root", default=None, help="Project root directory")
def children_cmd(id_: str, root: str | None):
    """List direct children of a component."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    entry = index["components"].get(id_)
    if not entry:
        raise click.ClickException(f"Component '{id_}' not found")
    children = entry.get("children", [])
    if not children:
        click.echo(f"{entry['name']} has no children")
        return
    click.echo(f"Children of {entry['name']}:")
    for child_id in children:
        child = index["components"][child_id]
        click.echo(f"  {child['name']} [{child['type']}] ({child_id})")
