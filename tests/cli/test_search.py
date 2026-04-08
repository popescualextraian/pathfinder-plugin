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
    save_component(d, {"id": "payment", "name": "Payment Gateway", "type": "service", "status": "active", "tags": ["pci-scope", "customer-facing"]})
    save_component(d, {"id": "auth", "name": "Auth Service", "type": "service", "status": "active", "tags": ["customer-facing"]})
    save_component(d, {"id": "ledger", "name": "Ledger", "type": "module", "status": "deprecated", "tags": ["pci-scope"]})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_search_by_name(runner, test_dir):
    result = runner.invoke(cli, ["search", "Payment", "--root", str(test_dir)])
    assert "Payment Gateway" in result.output
    assert "Auth" not in result.output


def test_search_by_tag(runner, test_dir):
    result = runner.invoke(cli, ["search", "--tag", "pci-scope", "--root", str(test_dir)])
    assert "Payment Gateway" in result.output
    assert "Ledger" in result.output
    assert "Auth" not in result.output


def test_search_by_type(runner, test_dir):
    result = runner.invoke(cli, ["search", "--type", "service", "--root", str(test_dir)])
    assert "Payment Gateway" in result.output
    assert "Auth Service" in result.output
    assert "Ledger" not in result.output
