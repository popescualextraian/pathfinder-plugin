import tempfile
import shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.cli.main import cli

@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def runner():
    return CliRunner()

def test_creates_pathfinder_directory(runner, test_dir):
    result = runner.invoke(cli, ["init", "--name", "Test Project", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert (test_dir / ".pathfinder").exists()
    assert "Initialized" in result.output

def test_fails_if_already_initialized(runner, test_dir):
    runner.invoke(cli, ["init", "--name", "Test", "--root", str(test_dir)])
    result = runner.invoke(cli, ["init", "--name", "Test", "--root", str(test_dir)])
    assert result.exit_code != 0
