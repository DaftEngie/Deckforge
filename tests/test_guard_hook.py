"""Regression tests for .claude/hooks/protect_paths.py (the local agent guard)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "protect_paths.py"


def decision(tool_name: str, **tool_input: str) -> str:
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
        env={"CLAUDE_PROJECT_DIR": str(ROOT), "PATH": ""},
    )
    if not result.stdout.strip():
        return "allow"
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_smoke.py",
        "ci/tamper_check.py",
        ".claude/settings.json",
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "src/../ci/tamper_check.py",
        "/home/deck/.steam/steam/config/config.vdf",
    ],
)
def test_protected_or_outside_paths_are_denied(path):
    assert decision("Edit", file_path=path) == "deny"


@pytest.mark.parametrize("path", ["src/deckforge/new_module.py", "tests/test_brand_new.py"])
def test_normal_paths_are_allowed(path):
    assert decision("Write", file_path=path) == "allow"


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf build/",
        'rm -rf "$HOME"',
        "rm -rf /tmp/../home/deck",
        "rm -r -f tests",
        "mv notes ~/",
        "pip install requests",
        "git push origin main",
        "gh pr merge 3",
        "sed -i s/a/b/ tests/test_smoke.py",
        "echo x > ci/tamper_check.py",
        "sudo systemctl stop sshd",
    ],
)
def test_dangerous_commands_are_denied(command):
    assert decision("Bash", command=command) == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "python -m pytest -q",
        'rm -rf "$TMPDIR/deckforge-abc"',
        "git push -u origin feat/profiles",
        "ruff check .",
    ],
)
def test_normal_commands_are_allowed(command):
    assert decision("Bash", command=command) == "allow"
