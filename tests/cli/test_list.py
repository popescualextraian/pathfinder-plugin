import tempfile, shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.core.storage import init_project, save_component
from pathfinder.core.index_builder import build_index
from pathfinder.cli.list_cmd import list_cmd
from pathfinder.cli.show_cmd import show_cmd, children_cmd
import click

@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "system", "name": "System", "type": "system", "status": "active"})
    save_component(d, {"id": "system.payment", "name": "Payment", "type": "module", "status": "active", "parent": "system"})
    save_component(d, {"id": "system.payment.gateway", "name": "Gateway", "type": "service", "status": "active", "parent": "system.payment"})
    save_component(d, {"id": "system.auth", "name": "Auth", "type": "module", "status": "active", "parent": "system"})
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def test_cli():
    """Standalone CLI group for testing without touching main.py."""
    grp = click.Group()
    grp.add_command(list_cmd)
    grp.add_command(show_cmd)
    grp.add_command(children_cmd)
    return grp

def test_shows_tree(runner, test_dir, test_cli):
    result = runner.invoke(test_cli, ["list", "--root", str(test_dir)])
    assert "System" in result.output
    assert "Payment" in result.output
    assert "Gateway" in result.output
    assert "Auth" in result.output

def test_truncates_at_level(runner, test_dir, test_cli):
    result = runner.invoke(test_cli, ["list", "--level", "1", "--root", str(test_dir)])
    assert "System" in result.output
    assert "Payment" in result.output
    assert "Gateway" not in result.output
