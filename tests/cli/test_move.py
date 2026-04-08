import tempfile, shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.cli.main import cli
from pathfinder.core.storage import load_component

@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    r = CliRunner()
    r.invoke(cli, ["init", "--name", "Test", "--root", str(d)])
    r.invoke(cli, ["add", "system", "System", "--root", str(d)])
    r.invoke(cli, ["add", "module", "Payment", "--parent", "system", "--root", str(d)])
    r.invoke(cli, ["add", "module", "Billing", "--parent", "system", "--root", str(d)])
    r.invoke(cli, ["add", "service", "Gateway", "--parent", "system.payment", "--root", str(d)])
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def runner():
    return CliRunner()

def test_moves_component(runner, test_dir):
    result = runner.invoke(cli, ["move", "system.payment.gateway", "--parent", "system.billing", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert "Moved" in result.output
    comp = load_component(test_dir, "system.billing.gateway")
    assert comp["parent"] == "system.billing"
