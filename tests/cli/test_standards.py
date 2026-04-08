import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_standards


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_shows_no_standards(runner, test_dir):
    result = runner.invoke(cli, ["standards", "--root", str(test_dir)])
    assert "No standards" in result.output


def test_shows_standards(runner, test_dir):
    save_standards(test_dir, {"spec": "All services must have health checks"})
    result = runner.invoke(cli, ["standards", "--root", str(test_dir)])
    assert "health checks" in result.output
