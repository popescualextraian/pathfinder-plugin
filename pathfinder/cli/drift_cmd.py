"""Drift check command."""

import sys
import glob as glob_module

import click

from pathfinder.core.index_builder import build_index, validate_index
from pathfinder.cli.utils import resolve_root


@click.group("drift")
def drift_group():
    """Drift detection commands."""
    pass


@drift_group.command("check")
@click.option("--ci", is_flag=True, help="Exit with code 1 if drift found")
@click.option("--root", default=None, help="Project root directory")
def drift_check_cmd(ci: bool, root: str | None):
    """Check for architectural drift."""
    project_root = resolve_root(root)
    issues = validate_index(project_root)
    index = build_index(project_root)

    # Check code mappings point to real files
    for comp in index["components"].values():
        for mapping in comp.get("codeMappings", []):
            matches = glob_module.glob(mapping["glob"], recursive=True)
            if not matches:
                issues.append({
                    "component_id": comp["id"],
                    "issue": f"Code mapping '{mapping['glob']}' matches no files",
                    "severity": "warning",
                })

    # Check for unmapped leaf components
    for comp in index["components"].values():
        if comp.get("external"):
            continue
        if not comp.get("codeMappings") and comp.get("children") == []:
            issues.append({
                "component_id": comp["id"],
                "issue": "Leaf component has no code mappings",
                "severity": "warning",
            })

    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    if not issues:
        click.echo("No drift detected. Architecture is clean.")
        return

    click.echo(f"Drift check: {len(errors)} error(s), {len(warnings)} warning(s)\n")
    for issue in issues:
        prefix = "ERROR" if issue["severity"] == "error" else "WARN"
        click.echo(f"  [{prefix}] {issue['component_id']}: {issue['issue']}")

    if ci and errors:
        sys.exit(1)
