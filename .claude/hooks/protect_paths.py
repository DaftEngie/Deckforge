#!/usr/bin/env python3
"""PreToolUse guard. Best-effort backup to permissions + sandbox (not a security boundary).

Blocks: edits to protected paths, modifying/deleting existing test files, recursive
deletes outside temp dirs, $HOME/~ as a delete/move target, dependency installs,
pushes to main, merges, sudo.
Denies by printing a PreToolUse JSON decision and exiting 0.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROTECTED_PREFIXES = (
    "evals/",
    "bench/",
    "ci/",
    ".github/",
    ".claude/",
    "tests/fixtures/golden/",
)
PROTECTED_FILES = ("pyproject.toml", "conftest.py")

BASH_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bsudo\b"), "sudo is not allowed in dev sessions (R6)."),
    (
        re.compile(r"\b(pip|pip3|uv|poetry|npm|pnpm|yarn)\s+(install|add)\b"),
        "Dependency installs are blocked (R8). Propose the dependency in the PR instead.",
    ),
    (
        re.compile(r"\bgit\s+push\b[^\n;&|]*\b(main|master)\b"),
        "Pushing to main is blocked (R9). Open a PR from a branch.",
    ),
    (re.compile(r"\bgh\s+pr\s+merge\b"), "Merging is Fede's decision (R9)."),
    (
        re.compile(r"\b(rm|mv)\b[^\n;&|]*(\$HOME|\$\{HOME\}|(^|\s)~(/|\s|$))"),
        "$HOME or ~ in a delete/move target is blocked (R6).",
    ),
]

RECURSIVE_RM = re.compile(r"\brm\s+((-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)\s+)")
SAFE_RM_TARGET = re.compile(r"^(\"|')?(/tmp/|\$TMPDIR|\$\{TMPDIR|\$tmp|\$\{tmp)", re.I)
WRITE_TO_PROTECTED = re.compile(
    r"(>|\btee\b|\bsed\s+-i\b|\bcp\b|\bmv\b|\btruncate\b)[^\n;&|]*\b("
    + "|".join(re.escape(p) for p in PROTECTED_PREFIXES + ("tests/",))
    + ")"
)


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def relative_to_project(path_str: str, project: Path) -> str | None:
    try:
        candidate = Path(path_str)
        if not candidate.is_absolute():
            candidate = project / candidate
        return candidate.resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        return None


def check_file_tool(tool_name: str, tool_input: dict, project: Path) -> None:
    path_str = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not path_str:
        return
    rel = relative_to_project(path_str, project)
    if rel is None:
        deny(f"Editing files outside the project is blocked (R7/R10): {path_str}")
    assert rel is not None
    if rel.startswith(PROTECTED_PREFIXES) or Path(rel).name in PROTECTED_FILES:
        deny(f"'{rel}' is protected (R5). Only Fede changes it. If it looks wrong, report BLOCKED.")
    if rel.startswith("tests/"):
        target = project / rel
        if target.exists():
            deny(
                f"'{rel}' is an existing test file and is read-only (R5). "
                "Add a new test file instead, or report BLOCKED if this test is wrong."
            )


def check_bash(command: str) -> None:
    for pattern, reason in BASH_RULES:
        if pattern.search(command):
            deny(reason)
    for match in RECURSIVE_RM.finditer(command):
        rest = command[match.end() :]
        rest = re.split(r"[;&|\n]", rest, maxsplit=1)[0]
        targets = [t for t in rest.split() if not t.startswith("-")]
        if not targets or not all(SAFE_RM_TARGET.match(t) for t in targets):
            deny(
                "Recursive delete outside a temp directory is blocked (R6). "
                "Create a dir with mktemp and delete only inside it."
            )
    if WRITE_TO_PROTECTED.search(command):
        deny("Shell writes into protected paths or tests/ are blocked (R5).")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return  # malformed input: fall through to normal permission flow
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if tool_name == "Bash":
        check_bash(tool_input.get("command", ""))
    elif tool_name in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
        check_file_tool(tool_name, tool_input, project)


if __name__ == "__main__":
    main()
