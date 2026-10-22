"""deckforge.measure.main + report shape: docs/specs/measure.md, M10-M12 + C2, C5, C12, C13, C15.

CONTRACTS (written from the spec before any implementation exists)

analyze(...) -> dict                                                              [C5]
  Postcondition: keys are exactly KEYS below; file is the base name.

main(argv=None) -> int                                                     [M10, M11, C12]
  Preconditions: argv is a list of strings (or None for sys.argv).
  Postconditions:
    - prints the text report (or, with --json, json.dumps(report, indent=2,
      sort_keys=True) + "\n") and returns 0, whatever the verdict.
    - on MeasureError: returns 2, prints exactly one line to stderr, no report.
    - argparse usage errors: argparse's own output, exit 2 (one-line rule exempt).
    - any other exception propagates.
    - a positional log wins over --logs-dir; otherwise the newest candidate in
      --logs-dir (default <home>/deckforge/logs): regular files by lstat, name ends
      with lowercase ".csv" and not "_summary.csv"; newest st_mtime_ns, ties to the
      name that sorts last; the logs folder itself may be a link and is followed;
      missing / not-a-folder / no candidates -> MeasureError; no fallback when the
      newest file fails to parse.
  Invariants: nothing under the logs folder is created, changed or deleted (content
  and mtimes); the module adds no logging handlers.                         [M12, C15]
"""

import json
import logging
import os

import pytest
from test_measure_support import (
    MS,
    S,
    START_NS,
    SYSTEM_NAMES,
    grid,
    interleave,
    log_text,
    row,
    run_cli,
    run_module,
    run_python,
    snapshot,
    sorted_markers,
    steady,
    write_log,
)

from deckforge import measure

KEYS = {
    "artifact_rows",
    "avg_fps",
    "bad_rows",
    "duration_s",
    "fg_multiplier",
    "file",
    "first_bad_line",
    "frames",
    "gpu_busy_share",
    "hitches",
    "limit",
    "low_0_1pct_fps",
    "low_1pct_fps",
    "median_fps",
    "real_avg_fps",
    "real_is_estimate",
    "real_low_1pct_fps",
    "reasons",
    "slower_than",
    "stalls",
    "system",
    "verdict",
    "warnings",
    "worst_window",
}
SYSTEM = {
    "os": "Steam Runtime 4",
    "cpu": "AMD Custom APU 0932",
    "gpu": "AMD Custom GPU 0932 (RADV VANGOGH)",
    "ram": "15159840",
    "kernel": "6.18.50-valve2-1-neptune-618-gc7289a96b14d",
    "driver": "",
    "cpuscheduler": "powersave",
}
T0 = 1_700_000_000_000_000_000  # a fixed mtime in ns


def json_report(capsys, argv):
    code, out, err = run_cli(measure, ["--json", *argv], capsys)
    assert code == 0, err
    return json.loads(out)


def assert_one_line_error(code, out, err):
    assert code == 2
    assert out == ""
    assert err.strip() != ""
    assert len(err.rstrip("\n").split("\n")) == 1


def log_at(folder, name, mtime_ns, lines=None):
    path = write_log(folder, steady(300) if lines is None else lines, name=name)
    os.utime(path, ns=(mtime_ns, mtime_ns))
    return path


# ---- C5 / M10: report shape and JSON ------------------------------------------------


def test_c5_analyze_key_set_is_exact(tmp_path):
    path = write_log(tmp_path, steady(300))
    r = measure.analyze(measure.parse_log(str(path)))
    assert set(r) == KEYS
    assert r["file"] == "session.csv"
    assert r["system"] == SYSTEM
    assert set(r["slower_than"]) == {"35", "30", "28"}
    assert set(r["worst_window"]) == {"start_s", "avg_fps", "low_1pct_fps"}


def test_c5_stall_entries_have_exactly_at_s_and_duration_s(tmp_path):
    lines = steady(10) + steady(10, start_ns=START_NS + 5 * S)
    r = measure.analyze(measure.parse_log(str(write_log(tmp_path, lines))))
    assert len(r["stalls"]) == 1
    assert set(r["stalls"][0]) == {"at_s", "duration_s"}


def test_m10_json_is_sorted_indented_with_trailing_newline(tmp_path, capsys):
    path = write_log(tmp_path, steady(300))
    expected = measure.analyze(measure.parse_log(str(path)))
    code, out, err = run_cli(measure, ["--json", str(path)], capsys)
    assert code == 0
    assert out == json.dumps(expected, indent=2, sort_keys=True) + "\n"
    assert set(json.loads(out)) == KEYS


def test_m10_json_file_is_base_name_and_fg_multiplier_is_reported(tmp_path, capsys):
    path = write_log(tmp_path, steady(300), name="Wilds_2026-10-21.csv")
    r = json_report(capsys, ["--fg-multiplier", "2", str(path)])
    assert r["file"] == "Wilds_2026-10-21.csv"
    assert r["fg_multiplier"] == 2
    assert r["real_is_estimate"] is True
    assert r["real_avg_fps"] == 20.0


def test_m10_wilds_shaped_log_full_report(tmp_path, capsys):
    # Spec end-to-end check: 7,428 rows over 299.9 s at 24.8 fps, gpu limited, fail.
    # Every frame 40.375 ms (exact in binary): avg = low = 24.7678 -> 24.8 shown,
    # 24.7 in reasons (floor). Two 2.2e7 artifacts near 6.1 s and 52.5 s whose
    # frametimes differ by exactly the elapsed gap, as in Fede's log.
    step = 40_375_000
    lines = [row(40.375, START_NS + k * step, gpu_load=99) for k in range(7428)]
    first = 21_987_654.0
    second = first + (1300 - 151) * 40.375
    lines.insert(1301, row(second, START_NS + 1300 * step + MS, gpu_load=99))
    lines.insert(152, row(first, START_NS + 151 * step + MS, gpu_load=99))
    path = write_log(tmp_path, lines, name="MonsterHunterWilds_2026-10-21_21-04-33.csv")
    r = json_report(capsys, [str(path)])
    assert r == {
        "artifact_rows": 2,
        "avg_fps": 24.8,
        "bad_rows": 0,
        "duration_s": 299.9,
        "fg_multiplier": 1,
        "file": "MonsterHunterWilds_2026-10-21_21-04-33.csv",
        "first_bad_line": None,
        "frames": 7428,
        "gpu_busy_share": 1.0,
        "hitches": 0,
        "limit": "gpu",
        "low_0_1pct_fps": 24.8,
        "low_1pct_fps": 24.8,
        "median_fps": 24.8,
        "real_avg_fps": 24.8,
        "real_is_estimate": False,
        "real_low_1pct_fps": 24.8,
        "reasons": ["average 24.7 fps is below 30", "1% low 24.7 fps is below 28"],
        "slower_than": {"35": 1.0, "30": 1.0, "28": 1.0},
        "stalls": [],
        "system": SYSTEM,
        "verdict": "fail",
        "warnings": ["artifact_rows"],
        "worst_window": {"start_s": 0.0, "avg_fps": 24.8, "low_1pct_fps": 24.8},
    }


def test_c2_empty_log_json_nulls_and_exit_0(tmp_path, capsys):
    path = write_log(tmp_path, [])
    r = json_report(capsys, [str(path)])
    assert r["frames"] == 0
    assert r["avg_fps"] is None
    assert r["worst_window"] is None
    assert r["slower_than"] == {}
    assert r["verdict"] == "not_enough_data"


# ---- M10: text report ---------------------------------------------------------------


def text_report(capsys, argv):
    code, out, err = run_cli(measure, argv, capsys)
    assert code == 0, err
    return out


def test_m10_text_report_shows_file_and_every_fps_value(tmp_path, capsys):
    # avg 56.8, median 62.5, 1% low 45.5, 0.1% low 28.6; real (x2) 28.4 and 22.7
    fill = (15.0, 16.0, 20.0, 22.0, 30.0, 35.0, 42.0)
    lines = grid(interleave(sorted_markers(1000, 499, 989, 998, fill)))
    path = write_log(tmp_path, lines, name="spot_a.csv")
    out = text_report(capsys, ["--fg-multiplier", "2", str(path)])
    for text in ["spot_a.csv", "56.8", "62.5", "45.5", "28.6", "28.4", "22.7"]:
        assert text in out, text


def test_m10_text_report_lists_reasons(tmp_path, capsys):
    path = write_log(tmp_path, steady(300, 50.0))
    out = text_report(capsys, ["--fg-multiplier", "2", str(path)])
    assert "average 20.0 fps is below 30" in out
    assert "1% low 20.0 fps is below 28" in out
    assert "real-frame 1% low 10.0 fps is below 14" in out


@pytest.mark.parametrize("fg", [2, 3])
def test_m5_text_says_estimated_with_multiplier(tmp_path, capsys, fg):
    path = write_log(tmp_path, steady(300))
    out = text_report(capsys, ["--fg-multiplier", str(fg), str(path)])
    assert f"estimated, assuming each real frame is shown {fg} times" in out


def test_m5_text_not_estimated_without_multiplier(tmp_path, capsys):
    out = text_report(capsys, [str(write_log(tmp_path, steady(300)))])
    assert "estimated" not in out


@pytest.mark.parametrize(
    ("loads", "sentence"),
    [
        ([95] * 10, "the graphics chip was the limit; graphics settings will raise fps"),
        (
            [40] * 10,
            "the graphics chip had room to spare; the limit was likely the processor, "
            "or a frame cap",
        ),
        ([95] * 5 + [10] * 5, "a mix"),
    ],
    ids=["gpu", "not_gpu", "mixed"],
)
def test_m6_text_limit_sentence(tmp_path, capsys, loads, sentence):
    path = write_log(tmp_path, grid([25.0] * len(loads), gpu_load=loads))
    assert sentence in text_report(capsys, [str(path)])


# ---- M10 / C12: exit codes ----------------------------------------------------------


@pytest.mark.parametrize("as_json", [False, True])
def test_m10_exit_0_for_fail_and_not_enough_data(tmp_path, capsys, as_json):
    flag = ["--json"] if as_json else []
    failing = write_log(tmp_path / "a", steady(300, 50.0))
    tiny = write_log(tmp_path / "b", steady(5))
    assert run_cli(measure, [*flag, str(failing)], capsys)[0] == 0
    assert run_cli(measure, [*flag, str(tiny)], capsys)[0] == 0


def test_m10_measure_error_missing_column_exit_2_one_line(tmp_path, capsys):
    path = tmp_path / "session.csv"
    path.write_text(log_text(["1,2"], columns=["fps", "frametime"]), encoding="utf-8")
    assert_one_line_error(*run_cli(measure, [str(path)], capsys))


def test_m10_measure_error_summary_file_exit_2_one_line(tmp_path, capsys):
    path = write_log(tmp_path, steady(300), name="session_summary.csv")
    assert_one_line_error(*run_cli(measure, ["--json", str(path)], capsys))


def test_m10_measure_error_not_a_regular_file_exit_2_one_line(tmp_path, capsys):
    folder = tmp_path / "folder.csv"
    folder.mkdir()
    assert_one_line_error(*run_cli(measure, [str(folder)], capsys))


@pytest.mark.parametrize("fg", ["0", "5", "-1"])
def test_m5_fg_multiplier_out_of_range_exit_2_one_line(tmp_path, capsys, fg):
    path = write_log(tmp_path, steady(300))
    assert_one_line_error(*run_cli(measure, ["--fg-multiplier", fg, str(path)], capsys))


@pytest.mark.parametrize(
    "argv", [["--fg-multiplier", "abc"], ["--fg-multiplier", "2.5"], ["--no-such-flag"]]
)
def test_c12_argparse_usage_error_exits_2(tmp_path, capsys, argv):
    path = write_log(tmp_path, steady(300))
    code, out, err = run_cli(measure, [*argv, str(path)], capsys)
    assert code == 2
    assert out == ""
    assert err != ""


def test_m10_other_exceptions_propagate(tmp_path, capsys, monkeypatch):
    def boom(path):
        raise RuntimeError("not a MeasureError")

    monkeypatch.setattr(measure, "parse_log", boom)
    with pytest.raises(RuntimeError, match="not a MeasureError"):
        measure.main([str(write_log(tmp_path, steady(300)))])


def test_m10_module_entry_point_exit_codes(tmp_path):
    good = run_module(["--json", str(write_log(tmp_path, steady(300)))])
    assert good.returncode == 0, good.stderr
    assert json.loads(good.stdout)["frames"] == 300
    bad = run_module(["--fg-multiplier", "9", str(tmp_path / "session.csv")])
    assert bad.returncode == 2
    assert len(bad.stderr.strip().splitlines()) == 1


# ---- M11 / C13: picking the log -----------------------------------------------------


def pick(capsys, logs_dir):
    return json_report(capsys, ["--logs-dir", str(logs_dir)])["file"]


def test_m11_newest_by_mtime(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "a.csv", T0 + 5 * S)
    log_at(logs, "b.csv", T0 + 10 * S)
    log_at(logs, "c.csv", T0)
    assert pick(capsys, logs) == "b.csv"


def test_m11_summary_file_is_skipped(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "a.csv", T0)
    log_at(logs, "a_summary.csv", T0 + 10 * S)
    assert pick(capsys, logs) == "a.csv"


def test_c13_uppercase_csv_and_other_names_ignored(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "a.csv", T0)
    log_at(logs, "z.CSV", T0 + 10 * S)
    log_at(logs, "z.txt", T0 + 10 * S)
    log_at(logs, "z.csv.bak", T0 + 10 * S)
    assert pick(capsys, logs) == "a.csv"


def test_m11_file_links_are_skipped(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "a.csv", T0)
    target = log_at(tmp_path / "elsewhere", "real.csv", T0 + 10 * S)
    link = logs / "z.csv"
    link.symlink_to(target)
    os.utime(link, ns=(T0 + 10 * S, T0 + 10 * S), follow_symlinks=False)
    assert pick(capsys, logs) == "a.csv"


def test_m11_folders_named_csv_are_skipped(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "a.csv", T0)
    sub = logs / "z.csv"
    sub.mkdir()
    os.utime(sub, ns=(T0 + 10 * S, T0 + 10 * S))
    assert pick(capsys, logs) == "a.csv"


def test_m11_mtime_tie_goes_to_name_that_sorts_last(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "b.csv", T0)
    log_at(logs, "a.csv", T0)
    log_at(logs, "B.csv", T0)  # "b" > "a" > "B"
    assert pick(capsys, logs) == "b.csv"


def test_c13_tie_is_compared_on_mtime_ns(tmp_path, capsys):
    logs = tmp_path / "logs"
    newer = log_at(logs, "a.csv", T0 + 1)
    older = log_at(logs, "b.csv", T0)
    # Fixture check: 1 ns apart, but equal as float seconds.
    assert newer.stat().st_mtime_ns - older.stat().st_mtime_ns == 1
    assert newer.stat().st_mtime == older.stat().st_mtime
    assert pick(capsys, logs) == "a.csv"


def test_c13_logs_folder_link_is_followed(tmp_path, capsys):
    real = tmp_path / "sdcard" / "logs"
    log_at(real, "a.csv", T0)
    link = tmp_path / "logs"
    link.symlink_to(real, target_is_directory=True)
    assert pick(capsys, link) == "a.csv"


def test_m11_no_candidates_exit_2(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "a_summary.csv", T0)
    log_at(logs, "notes.txt", T0)
    assert_one_line_error(*run_cli(measure, ["--logs-dir", str(logs)], capsys))


def test_m11_empty_folder_exit_2(tmp_path, capsys):
    logs = tmp_path / "logs"
    logs.mkdir()
    assert_one_line_error(*run_cli(measure, ["--logs-dir", str(logs)], capsys))


def test_m11_missing_folder_exit_2(tmp_path, capsys):
    missing = tmp_path / "nope"
    assert_one_line_error(*run_cli(measure, ["--logs-dir", str(missing)], capsys))


def test_c13_logs_dir_that_is_a_file_exit_2(tmp_path, capsys):
    not_dir = write_log(tmp_path, steady(300))
    assert_one_line_error(*run_cli(measure, ["--logs-dir", str(not_dir)], capsys))


def test_c13_newest_fails_to_parse_no_fallback(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "a.csv", T0)
    broken = logs / "b.csv"
    broken.write_text(SYSTEM_NAMES + "\nx\nfps,frametime\n1,2\n", encoding="utf-8")
    os.utime(broken, ns=(T0 + 10 * S, T0 + 10 * S))
    assert_one_line_error(*run_cli(measure, ["--logs-dir", str(logs)], capsys))


def test_c12_positional_log_wins_over_logs_dir(tmp_path, capsys):
    logs = tmp_path / "logs"
    log_at(logs, "newest.csv", T0 + 10 * S)
    chosen = log_at(tmp_path / "other", "chosen.csv", T0)
    r = json_report(capsys, ["--logs-dir", str(logs), str(chosen)])
    assert r["file"] == "chosen.csv"


def test_c12_positional_log_wins_even_if_logs_dir_is_missing(tmp_path, capsys):
    chosen = write_log(tmp_path, steady(300), name="chosen.csv")
    r = json_report(capsys, ["--logs-dir", str(tmp_path / "nope"), str(chosen)])
    assert r["file"] == "chosen.csv"


def test_m11_default_logs_dir_is_under_home(tmp_path, capsys):
    home = tmp_path / "home"
    log_at(home / "deckforge" / "logs", "a.csv", T0)
    assert json_report(capsys, ["--home", str(home)])["file"] == "a.csv"


# ---- M12 / C15: read-only -----------------------------------------------------------


def build_folder(tmp_path):
    logs = tmp_path / "logs"
    log_at(logs, "a.csv", T0)
    log_at(logs, "b.csv", T0 + S, steady(300) + [row("nan", START_NS + 300 * 25 * MS)])
    log_at(logs, "b_summary.csv", T0 + 2 * S)
    target = log_at(tmp_path / "elsewhere", "real.csv", T0)
    (logs / "link.csv").symlink_to(target)
    sub = logs / "sub"
    sub.mkdir()
    log_at(sub, "c.csv", T0)
    os.utime(sub, ns=(T0, T0))
    os.utime(logs, ns=(T0, T0))
    return logs


def test_m12_cli_leaves_folder_byte_for_byte_unchanged(tmp_path, capsys):
    logs = build_folder(tmp_path)
    before = snapshot(tmp_path)
    for argv in (
        ["--logs-dir", str(logs)],
        ["--json", "--logs-dir", str(logs)],
        ["--fg-multiplier", "2", str(logs / "a.csv")],
        ["--fg-multiplier", "0", str(logs / "a.csv")],  # error path too
        [str(logs / "b_summary.csv")],
        [str(logs / "link.csv")],
    ):
        run_cli(measure, argv, capsys)
    assert snapshot(tmp_path) == before


def test_m12_parse_and_analyze_leave_folder_unchanged(tmp_path):
    logs = build_folder(tmp_path)
    before = snapshot(tmp_path)
    measure.analyze(measure.parse_log(str(logs / "b.csv")), fg_multiplier=3)
    assert snapshot(tmp_path) == before


def test_c15_module_adds_no_logging_handlers_in_process(tmp_path, capsys):
    root_before = list(logging.getLogger().handlers)
    run_cli(measure, ["--json", str(write_log(tmp_path, steady(300)))], capsys)
    assert logging.getLogger().handlers == root_before
    for name, logger in logging.Logger.manager.loggerDict.items():
        if name.startswith("deckforge") and isinstance(logger, logging.Logger):
            assert logger.handlers == [], name


def test_c15_module_adds_no_logging_handlers_fresh_interpreter(tmp_path):
    # In a fresh interpreter the root logger starts with no handlers, so a
    # logging.basicConfig() call (a no-op under pytest) would show up here.
    path = write_log(tmp_path, steady(300))
    probe = (
        "import logging, sys\n"
        "from deckforge import measure\n"
        "code = measure.main(['--json', sys.argv[1]])\n"
        "count = len(logging.getLogger().handlers) + sum(\n"
        "    len(lg.handlers) for lg in logging.Logger.manager.loggerDict.values()\n"
        "    if isinstance(lg, logging.Logger))\n"
        "print('HANDLERS', code, count)\n"
    )
    result = run_python(["-c", probe, str(path)])
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "HANDLERS 0 0"
