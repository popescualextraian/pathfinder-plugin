"""Help command — workflow-oriented guide to pathfinder CLI."""

import click


HELP_TEXT = """\
Pathfinder — architecture-first skills and agent for AI-driven development.

The CLI maintains an architecture graph (.pathfinder/) that AI coding skills
consume as context and guardrails.

\033[1mSetup\033[0m
  init             Initialize a new .pathfinder/ project
  install          Install skills and agent into a target project
  standards        Show project architectural standards

\033[1mModeling Components\033[0m
  add              Add a component (type + name, optional --parent)
  set              Update fields (--status, --type, --tag, --spec, etc.)
  remove           Remove a component and its children
  move             Reparent a component

\033[1mContracts & Dependencies\033[0m
  contract-add     Define input/output contracts on a component
  contract-remove  Remove a contract
  depend           Add or remove a structural dependency
  flow-add         Add a data flow between two components

\033[1mCode Mappings\033[0m
  map              Map files to a component (--glob pattern)
  mapped           Find which component owns a file
  unmapped         List components with no code mappings

\033[1mQuerying\033[0m
  show             Show component details (or full tree if no ID)
  children         List direct children of a component
  list             Show the component tree (--level to limit depth)
  search           Search by name, --tag, --type, or --status
  info             Project summary (component counts, coverage)
  deps             Show what a component depends on
  dependents       Show what depends on a component
  flows            Show data flows for a component (or all)
  trace            Trace data flow path between two components

\033[1mValidation & Export\033[0m
  validate         Check structural integrity (--ci for exit code)
  drift            Detect drift between code and architecture
  export           Export graph as json, dot, or markdown

\033[1mTypical Workflow\033[0m
  pathfinder init --name myproject
  pathfinder add system "Payment Service"
  pathfinder add module "Gateway" --parent payment-service
  pathfinder map payment-service.gateway --glob "src/gateway/**/*.py"
  pathfinder depend payment-service.gateway --on auth.tokens
  pathfinder validate
  pathfinder export --format markdown

Run 'pathfinder <command> --help' for details on any command.
"""


@click.command("help")
def help_cmd():
    """Show usage guide with grouped commands and typical workflow."""
    click.echo(HELP_TEXT)
