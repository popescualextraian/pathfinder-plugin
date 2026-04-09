from click.testing import CliRunner
from pathfinder.cli.main import cli


@classmethod
def runner():
    return CliRunner()


def test_help_command_runs():
    result = CliRunner().invoke(cli, ["help"])
    assert result.exit_code == 0


def test_help_shows_grouped_sections():
    result = CliRunner().invoke(cli, ["help"])
    assert "Setup" in result.output
    assert "Modeling Components" in result.output
    assert "Contracts & Dependencies" in result.output
    assert "Code Mappings" in result.output
    assert "Querying" in result.output
    assert "Validation & Export" in result.output
    assert "Typical Workflow" in result.output


def test_help_shows_key_commands():
    result = CliRunner().invoke(cli, ["help"])
    for cmd in ["init", "add", "show", "map", "validate", "export", "depend"]:
        assert cmd in result.output


def test_help_shows_footer():
    result = CliRunner().invoke(cli, ["help"])
    assert "pathfinder <command> --help" in result.output
