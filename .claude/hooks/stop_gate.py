#!/usr/bin/env python3
"""Stop/SubagentStop gate: an agent can't finish while the test suite fails.

Blocks (exit 2) at most MAX_BLOCKS times per session, matching the two-repair-round
rule. After that it lets the agent stop but tells it to report BLOCKED; CI still
refuses to merge failing code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_BLOCKS = 2


def counter_file(session_id: str) -> Path:
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_") or "unknown"
    return Path(tempfile.gettempdir()) / f"deckforge-stopgate-{safe}"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    if not (project / "tests").is_dir():
        return
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x", "--no-header", "-p", "no:cacheprovider"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    counter = counter_file(str(payload.get("session_id", "")))
    if result.returncode in (0, 5):  # 5 = no tests collected
        counter.unlink(missing_ok=True)
        return
    blocks = int(counter.read_text()) if counter.exists() else 0
    tail = "\n".join(result.stdout.strip().splitlines()[-20:])
    if blocks < MAX_BLOCKS:
        counter.write_text(str(blocks + 1))
        print(
            f"Tests are failing, so you are not done (repair round {blocks + 1}/{MAX_BLOCKS}).\n"
            f"{tail}",
            file=sys.stderr,
        )
        sys.exit(2)
    counter.unlink(missing_ok=True)
    print(
        "Tests still fail after 2 repair rounds. Stop and report BLOCKED with the failing "
        "test names; do not claim completion.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
