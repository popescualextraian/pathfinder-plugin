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
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def runner():
    return CliRunner()

def test_removes_leaf_with_force(runner, test_dir):
    result = runner.invoke(cli, ["remove", "system.payment", "--force", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert "Removed" in result.output

def test_dry_run_shows_without_deleting(runner, test_dir):
    runner.invoke(cli, ["add", "service", "Gateway", "--parent", "system.payment", "--root", str(test_dir)])
    result = runner.invoke(cli, ["remove", "system.payment", "--dry-run", "--root", str(test_dir)])
    assert "Would remove" in result.output
    comp = load_component(test_dir, "system.payment")
    assert comp["name"] == "Payment"
