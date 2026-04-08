import tempfile
import shutil
from pathlib import Path
import pytest
from click.testing import CliRunner
from pathfinder.cli.main import cli


@pytest.fixture
def test_dir():
    d = Path(tempfile.mkdtemp(prefix="pathfinder-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def runner():
    return CliRunner()


def test_install_copies_skills(runner, test_dir):
    result = runner.invoke(cli, ["install", "--root", str(test_dir)])
    assert result.exit_code == 0
    skills_dir = test_dir / "skills"
    assert skills_dir.exists()
    expected = [
        "pathfinder-check",
        "pathfinder-define",
        "pathfinder-discover",
        "pathfinder-implement",
        "pathfinder-navigate",
    ]
    for name in expected:
        assert (skills_dir / name / "SKILL.md").exists(), f"Missing skill: {name}"


def test_install_copies_agent(runner, test_dir):
    result = runner.invoke(cli, ["install", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert (test_dir / "agents" / "system-architect.md").exists()


def test_install_custom_dirs(runner, test_dir):
    result = runner.invoke(cli, [
        "install", "--root", str(test_dir),
        "--skills-dir", ".claude/skills",
        "--agents-dir", ".claude/agents",
    ])
    assert result.exit_code == 0
    assert (test_dir / ".claude" / "skills" / "pathfinder-discover" / "SKILL.md").exists()
    assert (test_dir / ".claude" / "agents" / "system-architect.md").exists()


def test_install_overwrites_existing_skills(runner, test_dir):
    # First install
    runner.invoke(cli, ["install", "--root", str(test_dir)])
    # Write a marker into a skill file
    marker_file = test_dir / "skills" / "pathfinder-check" / "SKILL.md"
    marker_file.write_text("old content")
    # Second install should overwrite
    result = runner.invoke(cli, ["install", "--root", str(test_dir)])
    assert result.exit_code == 0
    assert marker_file.read_text() != "old content"


def test_install_output_shows_guidance(runner, test_dir):
    result = runner.invoke(cli, ["install", "--root", str(test_dir)])
    assert "Pathfinder installed successfully" in result.output
    assert "CLAUDE.md" in result.output
    assert "pathfinder-discover" in result.output
