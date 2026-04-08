import tempfile, shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.core.storage import init_project, save_component
from pathfinder.cli.deps_cmd import deps_cmd, dependents_cmd
import click

@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "PaymentRequest"}]})
    save_component(d, {"id": "payment", "name": "Payment", "type": "service", "status": "active",
        "dataFlows": [{"to": "ledger", "data": "Transaction"}]})
    save_component(d, {"id": "ledger", "name": "Ledger", "type": "service", "status": "active"})
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def test_cli():
    grp = click.Group()
    grp.add_command(deps_cmd)
    grp.add_command(dependents_cmd)
    return grp

def test_shows_dependencies(runner, test_dir, test_cli):
    result = runner.invoke(test_cli, ["deps", "order", "--root", str(test_dir)])
    assert "payment" in result.output

def test_shows_dependents(runner, test_dir, test_cli):
    result = runner.invoke(test_cli, ["dependents", "payment", "--root", str(test_dir)])
    assert "order" in result.output
