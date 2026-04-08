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
                        "dataFlows": [{"to": "ledger", "data": "Transaction", "protocol": "async"}]})
    save_component(d, {"id": "ledger", "name": "Ledger", "type": "service", "status": "active"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_shows_all_flows(runner, test_dir):
    result = runner.invoke(cli, ["flows", "--root", str(test_dir)])
    assert "payment" in result.output
    assert "ledger" in result.output
    assert "Transaction" in result.output


def test_shows_flows_for_component(runner, test_dir):
    result = runner.invoke(cli, ["flows", "payment", "--root", str(test_dir)])
    assert "Transaction" in result.output


def test_trace_finds_path(runner, test_dir):
    result = runner.invoke(cli, ["trace", "payment", "ledger", "--root", str(test_dir)])
    assert "payment" in result.output
    assert "ledger" in result.output


def test_flow_add_creates_flow(runner, test_dir):
    result = runner.invoke(cli, ["flow-add", "ledger", "payment", "--data", "Receipt", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "ledger")
    flows = comp.get("dataFlows", [])
    assert any(f["data"] == "Receipt" for f in flows)


def test_flow_add_with_pattern(runner, test_dir):
    result = runner.invoke(cli, ["flow-add", "payment", "ledger", "--data", "Event", "--protocol", "kafka", "--pattern", "publish", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    flow = next(f for f in comp.get("dataFlows", []) if f["data"] == "Event")
    assert flow["pattern"] == "publish"


def test_flows_displays_pattern(runner, test_dir):
    save_component(test_dir, {"id": "order", "name": "Order", "type": "service", "status": "active",
        "dataFlows": [{"to": "payment", "data": "OrderEvent", "protocol": "kafka", "pattern": "publish"}]})
    result = runner.invoke(cli, ["flows", "--root", str(test_dir)])
    assert "kafka/publish" in result.output


def test_flows_unknown_component_shows_error(runner, test_dir):
    result = runner.invoke(cli, ["flows", "nonexistent", "--root", str(test_dir)])
    assert "not found" in result.output
