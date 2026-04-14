from unittest.mock import patch, MagicMock
from pathlib import Path

from click.testing import CliRunner

from pathfinder.cli.main import cli


def _mock_run_success(*args, **kwargs):
    """Mock subprocess.run that always succeeds."""
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = ""
    mock.stderr = ""
    return mock


def _mock_run_docker_not_found(*args, **kwargs):
    """Mock subprocess.run where docker info fails."""
    cmd = args[0] if args else kwargs.get("args", [])
    mock = MagicMock()
    if cmd and cmd[0] == "docker" and cmd[1] == "info":
        mock.returncode = 1
        mock.stdout = ""
        mock.stderr = "Cannot connect to Docker daemon"
    else:
        mock.returncode = 0
        mock.stdout = ""
        mock.stderr = ""
    return mock


def test_start_fails_without_pathfinder_dir(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["start", "--root", str(tmp_path)])
    assert result.exit_code != 0
    assert ".pathfinder/" in result.output


@patch("pathfinder.cli.docker_cmd.subprocess.run")
def test_start_fails_without_docker(mock_run, tmp_path):
    (tmp_path / ".pathfinder").mkdir()
    mock_run.side_effect = _mock_run_docker_not_found
    runner = CliRunner()
    result = runner.invoke(cli, ["start", "--root", str(tmp_path)])
    assert result.exit_code != 0
    assert "Docker" in result.output


@patch("pathfinder.cli.docker_cmd.subprocess.run")
def test_start_launches_containers(mock_run, tmp_path):
    (tmp_path / ".pathfinder").mkdir()

    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        cmd = args[0] if args else kwargs.get("args", [])
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = ""
        mock.stderr = ""

        # docker inspect for container existence check should fail (not found)
        if cmd and "inspect" in cmd:
            mock.returncode = 1
            mock.stdout = ""

        return mock

    mock_run.side_effect = side_effect
    runner = CliRunner()
    result = runner.invoke(cli, ["start", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "pathfinder-server" in result.output
    assert "pathfinder-mcp" in result.output


@patch("pathfinder.cli.docker_cmd.subprocess.run")
def test_stop_stops_containers(mock_run):
    def side_effect(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "running"
        mock.stderr = ""
        return mock

    mock_run.side_effect = side_effect
    runner = CliRunner()
    result = runner.invoke(cli, ["stop"])
    assert result.exit_code == 0
    assert "stopped" in result.output or "Done" in result.output
