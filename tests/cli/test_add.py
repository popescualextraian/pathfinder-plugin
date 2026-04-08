import tempfile, shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.cli.main import cli
from pathfinder.core.storage import load_component

@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    CliRunner().invoke(cli, ["init", "--name", "Test", "--root", str(d)])
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def runner():
    return CliRunner()

def test_adds_root_component(runner, test_dir):
    result = runner.invoke(cli, ["add", "system", "My System", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert "Added" in result.output
    comp = load_component(test_dir, "my-system")
    assert comp["name"] == "My System"

def test_adds_child_with_parent(runner, test_dir):
    runner.invoke(cli, ["add", "system", "System", "--root", str(test_dir)])
    runner.invoke(cli, ["add", "module", "Payment", "--parent", "system", "--root", str(test_dir)])
    comp = load_component(test_dir, "system.payment")
    assert comp["parent"] == "system"

def test_adds_external_component(runner, test_dir):
    result = runner.invoke(cli, ["add", "service", "Stripe API", "--external", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "stripe-api")
    assert comp.get("external") is True


def test_accepts_predefined_type(runner, test_dir):
    result = runner.invoke(cli, ["add", "infrastructure", "Redis", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert "Added" in result.output


def test_prompts_for_unknown_type(runner, test_dir):
    result = runner.invoke(cli, ["add", "gateway", "API Gateway", "--root", str(test_dir)], input="y\n")
    assert result.exit_code == 0
    assert "Added" in result.output
    from pathfinder.core.storage import load_config
    config = load_config(test_dir)
    assert "gateway" in config.get("componentTypes", [])


def test_rejects_unknown_type_when_declined(runner, test_dir):
    result = runner.invoke(cli, ["add", "gateway", "API Gateway", "--root", str(test_dir)], input="n\n")
    assert result.exit_code != 0


def test_adds_component_with_spec(runner, test_dir):
    result = runner.invoke(cli, ["add", "service", "Payment", "--spec", "Handles payments", "--root", str(test_dir)])
    assert result.exit_code == 0
    comp = load_component(test_dir, "payment")
    assert comp["spec"] == "Handles payments"
