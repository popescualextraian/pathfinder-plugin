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
    init_project(d, "Test")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_no_drift_clean_project(runner, test_dir):
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "service", "status": "active"})
    result = runner.invoke(cli, ["drift", "check", "--root", str(test_dir)])
    assert result.exit_code == 0


def test_ci_flag_exits_nonzero_on_errors(runner, test_dir):
    save_component(test_dir, {"id": "broken", "name": "Broken", "type": "service", "status": "active", "parent": "missing"})
    result = runner.invoke(cli, ["drift", "check", "--ci", "--root", str(test_dir)])
    assert result.exit_code != 0

def test_skips_code_mapping_check_for_external(runner, test_dir):
    save_component(test_dir, {"id": "ext-stripe", "name": "Stripe", "type": "service",
        "status": "active", "external": True})
    result = runner.invoke(cli, ["drift", "check", "--root", str(test_dir)])
    assert "ext-stripe" not in result.output
