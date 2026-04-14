import json
from pathlib import Path

from click.testing import CliRunner

from pathfinder.cli.main import cli


def test_install_copies_skills(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--root", str(tmp_path)])
    assert result.exit_code == 0

    skills_dir = tmp_path / ".claude" / "skills"
    assert skills_dir.exists()

    # Should have our 2 skills
    skill_dirs = [d.name for d in skills_dir.iterdir() if d.is_dir()]
    assert "pathfinder-context" in skill_dirs
    assert "pathfinder-review" in skill_dirs


def test_install_copies_agents(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--root", str(tmp_path)])
    assert result.exit_code == 0

    agents_dir = tmp_path / ".claude" / "agents"
    assert agents_dir.exists()

    agent_files = [f.name for f in agents_dir.iterdir() if f.is_file()]
    assert "init-agent.md" in agent_files
    assert "system-architect.md" in agent_files


def test_install_configures_mcp(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--root", str(tmp_path)])
    assert result.exit_code == 0

    settings_file = tmp_path / ".claude" / "settings.local.json"
    assert settings_file.exists()

    settings = json.loads(settings_file.read_text())
    assert "mcpServers" in settings
    assert "structurizr" in settings["mcpServers"]
    assert settings["mcpServers"]["structurizr"]["type"] == "sse"
    assert settings["mcpServers"]["structurizr"]["url"] == "http://localhost:3000/mcp"


def test_install_preserves_existing_settings(tmp_path):
    # Pre-existing settings
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    settings_file = claude_dir / "settings.local.json"
    settings_file.write_text(json.dumps({"mcpServers": {"other": {"command": "other"}}}))

    runner = CliRunner()
    runner.invoke(cli, ["install", "--root", str(tmp_path)])

    settings = json.loads(settings_file.read_text())
    assert "other" in settings["mcpServers"]
    assert "structurizr" in settings["mcpServers"]


def test_install_output_shows_counts(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--root", str(tmp_path)])
    assert "2 skills" in result.output
    assert "2 agents" in result.output
    assert "MCP server config" in result.output
