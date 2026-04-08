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
    save_component(d, {
        "id": "payment", "name": "Payment", "type": "service",
        "status": "active", "tags": ["existing-tag"],
    })
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_updates_status(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--status", "deprecated", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert comp["status"] == "deprecated"


def test_adds_tag(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--tag", "pci-scope", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert "pci-scope" in comp["tags"]
    assert "existing-tag" in comp["tags"]


def test_updates_type(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--type", "module", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert comp["type"] == "module"


def test_removes_tag(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--remove-tag", "existing-tag", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert "existing-tag" not in comp.get("tags", [])


def test_sets_spec_inline(runner, test_dir):
    runner.invoke(cli, ["set", "payment", "--spec", "Handles all payment processing", "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert comp["spec"] == "Handles all payment processing"


def test_sets_spec_from_file(runner, test_dir, tmp_path):
    spec_file = tmp_path / "spec.md"
    spec_file.write_text("# Payment\nHandles payments via Stripe.")
    runner.invoke(cli, ["set", "payment", "--spec-file", str(spec_file), "--root", str(test_dir)])
    comp = load_component(test_dir, "payment")
    assert "Stripe" in comp["spec"]
