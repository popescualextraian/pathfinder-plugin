import tempfile, shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component, load_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "frontend", "name": "Frontend", "type": "module", "status": "active"})
    save_component(d, {"id": "design-system", "name": "Design System", "type": "library", "status": "active"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_adds_dependency(runner, test_dir):
    result = runner.invoke(cli, ["depend", "frontend", "design-system", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "frontend")
    assert "design-system" in comp.get("dependsOn", [])


def test_removes_dependency(runner, test_dir):
    save_component(test_dir, {"id": "frontend", "name": "Frontend", "type": "module", "status": "active",
        "dependsOn": ["design-system"]})
    result = runner.invoke(cli, ["depend", "frontend", "design-system", "--remove", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "frontend")
    assert "design-system" not in comp.get("dependsOn", [])


def test_rejects_unknown_target(runner, test_dir):
    result = runner.invoke(cli, ["depend", "frontend", "ghost", "--root", str(test_dir)])
    assert result.exit_code != 0


def test_no_duplicate_dependency(runner, test_dir):
    runner.invoke(cli, ["depend", "frontend", "design-system", "--root", str(test_dir)])
    runner.invoke(cli, ["depend", "frontend", "design-system", "--root", str(test_dir)])
    comp = load_component(test_dir, "frontend")
    assert comp.get("dependsOn", []).count("design-system") == 1
