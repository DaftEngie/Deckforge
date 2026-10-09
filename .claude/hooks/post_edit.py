#!/usr/bin/env python3
"""PostToolUse sensor: lint the edited Python file and feed short results back.

Exit 2 shows stderr to Claude (the edit already happened; this is feedback, not a block).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    path = (payload.get("tool_input") or {}).get("file_path", "")
    if not path.endswith(".py") or shutil.which("ruff") is None:
        return
    result = subprocess.run(
        ["ruff", "check", "--output-format", "concise", path],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        lines = result.stdout.strip().splitlines()[:15]
        print(
            "ruff found problems in the file you just edited. Fix them before continuing:\n"
            + "\n".join(lines),
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
