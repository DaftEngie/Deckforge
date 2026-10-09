"""Tests for ci/tamper_check.py — the gate that protects every other gate."""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "tamper_check", Path(__file__).resolve().parents[1] / "ci" / "tamper_check.py"
)
tc = importlib.util.module_from_spec(_spec)
sys.modules["tamper_check"] = tc  # dataclasses need the module registered before exec
_spec.loader.exec_module(tc)


def test_clean_change_has_no_violations():
    changes = tc.parse_name_status("A\tsrc/deckforge/new.py\nA\ttests/test_new.py\n")
    assert tc.find_violations(changes, 3, 4, "+def helper():\n") == []


def test_deleted_test_file_is_flagged():
    changes = tc.parse_name_status("D\ttests/test_old.py\n")
    assert any("existing test file D" in v for v in tc.find_violations(changes, 1, 1, ""))


def test_modified_test_file_is_flagged():
    changes = tc.parse_name_status("M\ttests/test_old.py\n")
    assert any("existing test file M" in v for v in tc.find_violations(changes, 1, 1, ""))


def test_renamed_test_file_is_flagged():
    changes = tc.parse_name_status("R100\ttests/test_a.py\ttests/test_b.py\n")
    assert any("tests/test_a.py" in v for v in tc.find_violations(changes, 1, 1, ""))


def test_test_count_drop_is_flagged():
    assert any("test count dropped" in v for v in tc.find_violations([], 5, 4, ""))


def test_protected_paths_are_flagged():
    for path in [
        "ci/tamper_check.py",
        ".claude/settings.json",
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "bench/runner.py",
        "tests/fixtures/golden/a.png",
    ]:
        changes = tc.parse_name_status(f"M\t{path}\n")
        assert any("protected path" in v for v in tc.find_violations(changes, 0, 0, "")), path


def test_added_suppressions_are_flagged():
    diff = "\n".join(
        [
            "+++ b/src/x.py",
            "+@pytest.mark.skip(reason='flaky')",
            "+    pytest.xfail('later')",
            "+x = 1  # noqa: E501",
            "+run(cmd)  # nosec",
            "+y: int = 'a'  # type: ignore",
            "-old = 1  # noqa",
        ]
    )
    hits = tc.added_suppressions(diff)
    assert len(hits) == 5


def test_count_tests_counts_sync_and_async():
    src = "def test_a():\n    pass\nasync def test_b():\n    pass\ndef helper_test():\n    pass\n"
    assert tc.count_tests([src]) == 2
