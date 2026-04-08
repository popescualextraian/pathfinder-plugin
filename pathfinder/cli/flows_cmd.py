"""Flows commands — flows, trace, flow-add."""

import click

from pathfinder.core.storage import load_component, save_component
from pathfinder.core.index_builder import build_index
from pathfinder.core.graph import get_flows_for_component, trace_flow
from pathfinder.cli.utils import resolve_root


@click.command("flows")
@click.argument("id_", required=False)
@click.option("--root", default=None, help="Project root directory")
def flows_cmd(id_, root):
    """Show data flows (all or for a specific component)."""
    project_root = resolve_root(root)
    index = build_index(project_root)

    if id_:
        flows = get_flows_for_component(index, id_)
    else:
        flows = index["flows"]

    if not flows:
        click.echo("No data flows found")
        return

    click.echo(f"Data flows ({len(flows)}):")
    for flow in flows:
        protocol = flow.get("protocol", "")
        pattern = flow.get("pattern", "")
        if protocol and pattern:
            suffix = f" [{protocol}/{pattern}]"
        elif protocol:
            suffix = f" [{protocol}]"
        elif pattern:
            suffix = f" [{pattern}]"
        else:
            suffix = ""
        click.echo(f"  {flow['from']} \u2192 {flow['to']}: {flow['data']}{suffix}")


@click.command("trace")
@click.argument("from_id")
@click.argument("to_id")
@click.option("--root", default=None, help="Project root directory")
def trace_cmd(from_id, to_id, root):
    """Trace data flow path between two components."""
    project_root = resolve_root(root)
    index = build_index(project_root)
    path = trace_flow(index, from_id, to_id)

    if not path:
        click.echo(f"No path found from {from_id} to {to_id}")
        return

    click.echo(f"Flow path: {' \u2192 '.join(path)}")


@click.command("flow-add")
@click.argument("from_id")
@click.argument("to_id")
@click.option("--data", required=True, help="Description of data that flows")
@click.option("--protocol", default=None, help="Protocol (e.g., REST, async)")
@click.option("--pattern", default=None, help="Pattern (e.g., publish, subscribe)")
@click.option("--root", default=None, help="Project root directory")
def flow_add_cmd(from_id, to_id, data, protocol, pattern, root):
    """Add a data flow between components."""
    project_root = resolve_root(root)
    component = load_component(project_root, from_id)
    flows = component.get("dataFlows", [])
    new_flow = {"to": to_id, "data": data}
    if protocol:
        new_flow["protocol"] = protocol
    if pattern:
        new_flow["pattern"] = pattern
    flows.append(new_flow)
    component["dataFlows"] = flows
    save_component(project_root, component)
    build_index(project_root)
    click.echo(f"Added flow: {from_id} \u2192 {to_id} ({data})")
