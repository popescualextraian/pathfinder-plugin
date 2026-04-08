import tempfile, shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.core.storage import init_project, save_component
from pathfinder.cli.show_cmd import show_cmd, children_cmd
import click

@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    init_project(d, "Test")
    save_component(d, {"id": "payment", "name": "Payment", "type": "module", "status": "active",
        "spec": "Handles all payment processing",
        "contracts": {"inputs": [{"name": "ProcessPayment", "format": "POST /api/payments", "source": "order"}],
                      "outputs": [{"name": "PaymentResult", "format": "{ status }", "target": "order"}]},
        "dataFlows": [{"to": "ledger", "data": "Transaction", "protocol": "async"}],
        "tags": ["pci-scope"]})
    save_component(d, {"id": "payment.gateway", "name": "Gateway", "type": "service", "status": "active", "parent": "payment"})
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def test_cli():
    grp = click.Group()
    grp.add_command(show_cmd)
    grp.add_command(children_cmd)
    return grp

def test_shows_full_details(runner, test_dir, test_cli):
    result = runner.invoke(test_cli, ["show", "payment", "--root", str(test_dir)])
    assert "Payment" in result.output
    assert "Handles all payment processing" in result.output
    assert "pci-scope" in result.output

def test_shows_only_contracts(runner, test_dir, test_cli):
    result = runner.invoke(test_cli, ["show", "payment", "--contracts", "--root", str(test_dir)])
    assert "ProcessPayment" in result.output
    assert "PaymentResult" in result.output

def test_children_lists_direct_children(runner, test_dir, test_cli):
    result = runner.invoke(test_cli, ["children", "payment", "--root", str(test_dir)])
    assert "Gateway" in result.output

def test_shows_contract_version(runner, test_dir):
    save_component(test_dir, {"id": "checkout", "name": "Checkout", "type": "service", "status": "active",
        "contracts": {"outputs": [{"name": "OrderCreated", "format": "{orderId, total}", "version": "2.0"}]}})
    grp = click.Group()
    grp.add_command(show_cmd)
    result = runner.invoke(grp, ["show", "checkout", "--contracts", "--root", str(test_dir)])
    assert "2.0" in result.output
