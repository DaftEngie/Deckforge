#!/usr/bin/env python3
"""CI gate: detect changes that weaken the test suite or touch protected paths.

Fails (exit 1) when a PR, compared with its base:
  - deletes or modifies an existing file under tests/   (unless override)
  - lowers the number of test functions                   (unless override)
  - adds skip/xfail markers or lint/security suppressions (unless override)
  - touches protected paths (ci/, .claude/, .github/, bench/, evals/, pyproject.toml,
    tests/fixtures/golden/)                                (unless override)

Override: run with --override (CI passes it only when Fede applied the label
`test-change-approved`). Overrides are printed so they show up in the evidence pack.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass

PROTECTED_PREFIXES = (
    "ci/",
    ".claude/",
    ".github/",
    "bench/",
    "evals/",
    "tests/fixtures/golden/",
)
PROTECTED_FILES = ("pyproject.toml",)
TEST_FUNC = re.compile(r"^\s*(async\s+)?def\s+test_\w*\s*\(", re.M)
SUPPRESSION = re.compile(
    r"pytest\.mark\.(skip|skipif|xfail)|pytest\.(skip|xfail)\(|#\s*noqa|#\s*nosec|#\s*type:\s*ignore|#\s*pragma:\s*no\s*cover"
)


@dataclass(frozen=True)
class Change:
    status: str  # A, M, D, R
    path: str
    old_path: str | None = None


def parse_name_status(text: str) -> list[Change]:
    changes: list[Change] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        code = parts[0][0]
        if code == "R" and len(parts) == 3:
            changes.append(Change("R", parts[2], parts[1]))
        elif len(parts) >= 2:
            changes.append(Change(code, parts[1]))
    return changes


def is_protected(path: str) -> bool:
    return path.startswith(PROTECTED_PREFIXES) or path in PROTECTED_FILES


def count_tests(sources: list[str]) -> int:
    return sum(len(TEST_FUNC.findall(src)) for src in sources)


def added_suppressions(diff_text: str) -> list[str]:
    hits = []
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++") and SUPPRESSION.search(line):
            hits.append(line[1:].strip())
    return hits


def find_violations(
    changes: list[Change], base_test_count: int, head_test_count: int, diff_text: str
) -> list[str]:
    violations: list[str] = []
    for ch in changes:
        touched = [ch.path] + ([ch.old_path] if ch.old_path else [])
        if any(p.startswith("tests/") for p in touched) and ch.status in {"D", "M", "R"}:
            violations.append(f"existing test file {ch.status}: {ch.old_path or ch.path}")
        for p in touched:
            if is_protected(p):
                violations.append(f"protected path changed: {p}")
    if head_test_count < base_test_count:
        violations.append(f"test count dropped: {base_test_count} -> {head_test_count}")
    for hit in added_suppressions(diff_text):
        violations.append(f"suppression/skip added: {hit}")
    return sorted(set(violations))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def test_sources_at(ref: str) -> list[str]:
    files = [
        f
        for f in git("ls-tree", "-r", "--name-only", ref, "--", "tests").splitlines()
        if f.endswith(".py")
    ]
    return [git("show", f"{ref}:{f}") for f in files]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="base ref, e.g. origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--override", action="store_true")
    args = parser.parse_args(argv)

    merge_base = git("merge-base", args.base, args.head).strip()
    changes = parse_name_status(git("diff", "--name-status", "-M", merge_base, args.head))
    diff_text = git("diff", "-U0", merge_base, args.head, "--", "*.py")
    violations = find_violations(
        changes,
        count_tests(test_sources_at(merge_base)),
        count_tests(test_sources_at(args.head)),
        diff_text,
    )
    if not violations:
        print("tamper check: OK")
        return 0
    header = "tamper check: OVERRIDDEN by label" if args.override else "tamper check: FAILED"
    print(header)
    for v in violations:
        print(f"  - {v}")
    return 0 if args.override else 1


if __name__ == "__main__":
    sys.exit(main())
