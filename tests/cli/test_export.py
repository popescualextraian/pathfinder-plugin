import tempfile
import shutil
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "system", "name": "System", "type": "system", "status": "active"})
    save_component(d, {"id": "payment", "name": "Payment", "type": "module", "status": "active", "parent": "system",
                        "dataFlows": [{"to": "ledger", "data": "Transaction"}]})
    save_component(d, {"id": "ledger", "name": "Ledger", "type": "service", "status": "active", "parent": "system"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_export_json(runner, test_dir):
    result = runner.invoke(cli, ["export", "--format", "json", "--root", str(test_dir)])
    data = json.loads(result.output)
    assert "components" in data
    assert "system" in data["components"]


def test_export_dot(runner, test_dir):
    result = runner.invoke(cli, ["export", "--format", "dot", "--root", str(test_dir)])
    assert "digraph" in result.output
    assert "payment" in result.output


def test_export_markdown(runner, test_dir):
    result = runner.invoke(cli, ["export", "--format", "markdown", "--root", str(test_dir)])
    assert "System" in result.output
    assert "Payment" in result.output
