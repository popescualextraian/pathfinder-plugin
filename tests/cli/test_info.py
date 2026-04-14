from unittest.mock import patch, MagicMock

import yaml
from click.testing import CliRunner

from pathfinder.cli.main import cli


def test_info_no_pathfinder_dir(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["info", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "No .pathfinder/" in result.output


@patch("pathfinder.cli.info_cmd.subprocess.run")
def test_info_shows_project_details(mock_run, tmp_path):
    # Setup .pathfinder dir
    pf_dir = tmp_path / ".pathfinder"
    pf_dir.mkdir()
    (pf_dir / "config.yaml").write_text(yaml.dump({"project_name": "My App"}))
    (pf_dir / "workspace.dsl").write_text("workspace {}")
    (pf_dir / "practices.md").write_text("# Practices")

    mock = MagicMock()
    mock.returncode = 1  # containers not found
    mock.stdout = ""
    mock_run.return_value = mock

    runner = CliRunner()
    result = runner.invoke(cli, ["info", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "My App" in result.output
    assert "workspace.dsl" in result.output
    assert "Practices: found" in result.output
