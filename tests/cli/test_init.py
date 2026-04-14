import yaml
from click.testing import CliRunner

from pathfinder.cli.main import cli


def test_init_creates_pathfinder_dir(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--name", "Test Project", "--root", str(tmp_path)])
    assert result.exit_code == 0

    pf_dir = tmp_path / ".pathfinder"
    assert pf_dir.exists()
    assert (pf_dir / "workspace.dsl").exists()
    assert (pf_dir / "config.yaml").exists()
    assert (pf_dir / "practices.md").exists()


def test_init_config_contains_project_name(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["init", "--name", "My App", "--root", str(tmp_path)])

    config = yaml.safe_load((tmp_path / ".pathfinder" / "config.yaml").read_text())
    assert config["project_name"] == "My App"


def test_init_workspace_contains_project_name(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["init", "--name", "My App", "--root", str(tmp_path)])

    dsl = (tmp_path / ".pathfinder" / "workspace.dsl").read_text()
    assert 'workspace "My App"' in dsl
    assert "!identifiers hierarchical" in dsl


def test_init_practices_has_default_content(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["init", "--name", "Test", "--root", str(tmp_path)])

    practices = (tmp_path / ".pathfinder" / "practices.md").read_text()
    assert "KISS" in practices
    assert "Single Responsibility" in practices


def test_init_fails_if_already_exists(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["init", "--name", "Test", "--root", str(tmp_path)])

    result = runner.invoke(cli, ["init", "--name", "Test", "--root", str(tmp_path)])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_init_requires_name(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--root", str(tmp_path)])
    assert result.exit_code != 0
