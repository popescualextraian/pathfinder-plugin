import tempfile
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from pathfinder.cli.main import cli
from pathfinder.core.storage import init_project, save_component, load_component


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "payment", "name": "Payment", "type": "service", "status": "active",
                        "codeMappings": [{"glob": "src/payment/*.py"}]})
    save_component(d, {"id": "auth", "name": "Auth", "type": "service", "status": "active"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_map_adds_code_mapping(runner, test_dir):
    result = runner.invoke(cli, ["map", "auth", "--glob", "src/auth/**/*.py", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "auth")
    assert any(m["glob"] == "src/auth/**/*.py" for m in comp.get("codeMappings", []))


def test_mapped_finds_component(runner, test_dir):
    result = runner.invoke(cli, ["mapped", "src/payment/handler.py", "--root", str(test_dir)])
    assert "Payment" in result.output


def test_unmapped_lists_components_without_mappings(runner, test_dir):
    result = runner.invoke(cli, ["unmapped", "--root", str(test_dir)])
    assert "Auth" in result.output
    assert "Payment" not in result.output
