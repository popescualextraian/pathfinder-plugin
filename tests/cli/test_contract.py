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
    save_component(d, {"id": "payment", "name": "Payment", "type": "service", "status": "active"})
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_adds_input_contract(runner, test_dir):
    result = runner.invoke(cli, ["contract-add", "payment", "--input",
        "--name", "PaymentRequest", "--format", "POST /pay {amount}", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    inputs = comp.get("contracts", {}).get("inputs", [])
    assert any(c["name"] == "PaymentRequest" for c in inputs)


def test_adds_output_contract(runner, test_dir):
    result = runner.invoke(cli, ["contract-add", "payment", "--output",
        "--name", "PaymentResult", "--format", "{status, txId}", "--version", "2.0", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    outputs = comp.get("contracts", {}).get("outputs", [])
    out = next(c for c in outputs if c["name"] == "PaymentResult")
    assert out["version"] == "2.0"


def test_adds_contract_with_source(runner, test_dir):
    result = runner.invoke(cli, ["contract-add", "payment", "--input",
        "--name", "OrderData", "--format", "{orderId}", "--source", "order-service", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    inp = comp["contracts"]["inputs"][0]
    assert inp["source"] == "order-service"


def test_removes_contract(runner, test_dir):
    save_component(test_dir, {"id": "payment", "name": "Payment", "type": "service", "status": "active",
        "contracts": {"inputs": [{"name": "PaymentRequest", "format": "POST /pay"}], "outputs": []}})
    result = runner.invoke(cli, ["contract-remove", "payment", "--name", "PaymentRequest", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    inputs = comp.get("contracts", {}).get("inputs", [])
    assert not any(c["name"] == "PaymentRequest" for c in inputs)


def test_requires_input_or_output_flag(runner, test_dir):
    result = runner.invoke(cli, ["contract-add", "payment",
        "--name", "X", "--format", "Y", "--root", str(test_dir)])
    assert result.exit_code != 0
