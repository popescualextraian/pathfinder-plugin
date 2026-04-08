import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_no_issues_for_valid_graph(runner, test_dir):
    save_component(test_dir, {"id": "system", "name": "System", "type": "system", "status": "active"})
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "module", "status": "active", "parent": "system"})
    result = runner.invoke(cli, ["validate", "--root", str(test_dir)])
    assert "No issues" in result.output


def test_reports_broken_parent(runner, test_dir):
    save_component(test_dir, {"id": "orphan", "name": "Orphan", "type": "service", "status": "active", "parent": "nonexistent"})
    result = runner.invoke(cli, ["validate", "--root", str(test_dir)])
    assert "nonexistent" in result.output
    assert "does not exist" in result.output


def test_reports_broken_flow_target(runner, test_dir):
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "service", "status": "active",
                                "dataFlows": [{"to": "ghost", "data": "Something"}]})
    result = runner.invoke(cli, ["validate", "--root", str(test_dir)])
    assert "ghost" in result.output


def test_reports_broken_depends_on_target(runner, test_dir):
    save_component(test_dir, {"id": "app", "name": "App", "type": "module", "status": "active",
        "dependsOn": ["ghost"]})
    result = runner.invoke(cli, ["validate", "--root", str(test_dir)])
    assert "ghost" in result.output


def test_ci_exits_with_code_1(runner, test_dir):
    save_component(test_dir, {"id": "broken", "name": "Broken", "type": "service", "status": "active", "parent": "missing"})
    result = runner.invoke(cli, ["validate", "--ci", "--root", str(test_dir)])
    assert result.exit_code != 0
