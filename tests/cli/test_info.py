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
    init_project(d, "Test Project")
    save_component(d, {"id": "system", "name": "System", "type": "system", "status": "active"})
    save_component(d, {"id": "payment", "name": "Payment", "type": "module", "status": "active", "parent": "system",
                        "dataFlows": [{"to": "ledger", "data": "Transaction"}]})
    save_component(d, {"id": "ledger", "name": "Ledger", "type": "service", "status": "active", "parent": "system"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_shows_project_summary(runner, test_dir):
    result = runner.invoke(cli, ["info", "--root", str(test_dir)])
    assert "Test Project" in result.output
    assert "3" in result.output
    assert "1" in result.output
