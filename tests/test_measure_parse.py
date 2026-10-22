"""deckforge.measure.parse_log: spec docs/specs/measure.md, M1 + clarifier answers 8, 9, 14.

CONTRACTS (written from the spec before any implementation exists)

parse_log(path) -> MangoLog
  Preconditions (each violation raises MeasureError with one clear message):
    - path exists (else MeasureError).                                          [C17]
    - lstat(path) shows a regular file (links, folders, FIFOs, sockets, devices refused),
      checked before opening, so a FIFO never blocks.                           [M1, C14]
    - lstat size <= 64 MiB (exactly 64 MiB is allowed).                          [M1, C14]
    - the name does not end with "_summary.csv"; the message says to pass the frame
      log instead.                                                              [M1]
    - the bytes are valid UTF-8.                                                [M1]
    - at least 3 lines; line 3 has fps, frametime, elapsed; no duplicate names. [M1, C9]
  Postconditions:
    - MangoLog is a frozen dataclass with exactly: path, system, columns, rows,
      bad_rows, first_bad_line.
    - system maps line 1 names to line 2 values; {} on a length mismatch.
    - columns == line 3 split on commas (a UTF-8 BOM on line 1 is removed; CRLF accepted).
    - rows: every non-bad data row, in file order, as {column: float}; artifact rows
      are included (classifying them is analyze's job).                     [C17]
    - bad_rows counts rows with a wrong field count, a field that fails float(), a NaN
      or infinite field, frametime <= 0, elapsed < 0, or elapsed lower than the
      previous non-bad row's.                                                   [M1, C8]
    - first_bad_line is the 1-based file line of the first bad row, else None.
    - Whitespace-only lines are skipped and are never bad rows.                  [C9]
  Invariants: reads only; never writes (see test_measure_cli.py, M12).
"""

import dataclasses
import os
import socket

import pytest
from test_measure_support import (
    COLUMNS,
    MS,
    S,
    START_NS,
    SYSTEM_NAMES,
    SYSTEM_VALUES,
    log_text,
    row,
    run_module,
    steady,
    write_log,
)

from deckforge import measure

MIB_64 = 64 * 1024 * 1024
EXPECTED_SYSTEM = {
    "os": "Steam Runtime 4",
    "cpu": "AMD Custom APU 0932",
    "gpu": "AMD Custom GPU 0932 (RADV VANGOGH)",
    "ram": "15159840",
    "kernel": "6.18.50-valve2-1-neptune-618-gc7289a96b14d",
    "driver": "",
    "cpuscheduler": "powersave",
}
SPEC_EXAMPLE_ROW = (
    "185.568,5.38885,80.4233,8.0826,89,75,66,958,800,0.926651,2,8.68896,0.375156,0,3403,10423837"
)


def parse(tmp_path, lines, **kw):
    return measure.parse_log(str(write_log(tmp_path, lines, **kw)))


def assert_refused(path):
    with pytest.raises(measure.MeasureError):
        measure.parse_log(str(path))


# ---- M1: happy path ---------------------------------------------------------------


def test_m1_spec_example_row_parses_exactly(tmp_path):
    path = write_log(tmp_path, [SPEC_EXAMPLE_ROW])
    log = measure.parse_log(str(path))
    assert log.path == str(path)
    assert log.system == EXPECTED_SYSTEM
    assert log.columns == COLUMNS
    assert log.bad_rows == 0
    assert log.first_bad_line is None
    assert len(log.rows) == 1
    first = log.rows[0]
    assert set(first) == set(COLUMNS)
    assert all(isinstance(v, float) for v in first.values())
    assert first["fps"] == 185.568
    assert first["frametime"] == 5.38885
    assert first["gpu_load"] == 89.0
    assert first["elapsed"] == 10423837.0


def test_m1_rows_kept_in_file_order(tmp_path):
    log = parse(tmp_path, [row(25.0, START_NS), row(30.0, START_NS + 25 * MS)])
    assert [r["frametime"] for r in log.rows] == [25.0, 30.0]
    assert [r["elapsed"] for r in log.rows] == [float(START_NS), float(START_NS + 25 * MS)]


def test_m1_mangolog_is_frozen_dataclass_with_spec_fields(tmp_path):
    log = parse(tmp_path, steady(2))
    assert isinstance(log, measure.MangoLog)
    assert dataclasses.is_dataclass(log)
    names = {f.name for f in dataclasses.fields(log)}
    assert names == {"path", "system", "columns", "rows", "bad_rows", "first_bad_line"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        log.bad_rows = 5


def test_m1_measure_error_is_an_exception():
    assert issubclass(measure.MeasureError, Exception)


def test_m1_only_required_columns_are_needed(tmp_path):
    cols = ["fps", "frametime", "elapsed"]
    lines = [row(25.0, 0, columns=cols), row(25.0, 25 * MS, columns=cols)]
    log = parse(tmp_path, lines, columns=cols)
    assert log.columns == cols
    assert len(log.rows) == 2
    assert log.bad_rows == 0


def test_m1_header_only_has_no_rows(tmp_path):
    log = parse(tmp_path, [])
    assert log.rows == []
    assert log.bad_rows == 0
    assert log.first_bad_line is None


def test_m1_system_length_mismatch_gives_empty_dict(tmp_path):
    log = parse(tmp_path, steady(2), system_values="Steam Runtime 4,AMD Custom APU 0932")
    assert log.system == {}
    assert len(log.rows) == 2


# ---- M1: refusals -----------------------------------------------------------------


@pytest.mark.parametrize("missing", ["fps", "frametime", "elapsed"])
def test_m1_missing_required_column_raises(tmp_path, missing):
    cols = [c for c in COLUMNS if c != missing]
    lines = [",".join(["1"] * len(cols))]
    path = tmp_path / "session.csv"
    path.write_text(log_text(lines, columns=cols), encoding="utf-8")
    assert_refused(path)


@pytest.mark.parametrize(
    "content",
    ["", SYSTEM_NAMES + "\n", SYSTEM_NAMES + "\n" + SYSTEM_VALUES + "\n"],
    ids=["zero_lines", "one_line", "two_lines"],
)
def test_m1_fewer_than_three_lines_raises(tmp_path, content):
    path = tmp_path / "session.csv"
    path.write_text(content, encoding="utf-8")
    assert_refused(path)


def test_m1_invalid_utf8_raises(tmp_path):
    path = write_log(tmp_path, steady(3))
    path.write_bytes(path.read_bytes() + b"25.0,\xff\xfe,1\n")
    assert_refused(path)


def test_m1_summary_csv_refused_and_message_points_to_frame_log(tmp_path):
    path = write_log(tmp_path, steady(300), name="session_summary.csv")
    with pytest.raises(measure.MeasureError) as excinfo:
        measure.parse_log(str(path))
    assert "frame log" in str(excinfo.value).lower()


def test_c17_nonexistent_path_raises(tmp_path):
    assert_refused(tmp_path / "no_such_log.csv")


def test_c17_rows_include_artifact_rows(tmp_path):
    artifact = 22_000_000.0
    lines = [row(artifact, START_NS)]  # first row: an artifact
    lines += [row(25.0, START_NS + 25 * MS), row(artifact, START_NS + 50 * MS)]
    lines.append(row(25.0, START_NS + 75 * MS))
    log = parse(tmp_path, lines)
    assert log.bad_rows == 0
    assert [r["frametime"] for r in log.rows] == [artifact, 25.0, artifact, 25.0]


def test_m1_directory_is_not_a_regular_file(tmp_path):
    folder = tmp_path / "folder.csv"
    folder.mkdir()
    assert_refused(folder)


def test_m1_link_to_valid_log_is_refused(tmp_path):
    target = write_log(tmp_path / "real", steady(300))
    link = tmp_path / "link.csv"
    link.symlink_to(target)
    measure.parse_log(str(target))  # the target itself is fine
    assert_refused(link)


def test_c14_socket_is_not_a_regular_file(tmp_path):
    path = tmp_path / "s.csv"
    assert len(str(path)) < 100, "unix socket paths must stay under the 108-byte limit"
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.bind(str(path))
        assert_refused(path)
    finally:
        sock.close()


def test_c14_device_is_not_a_regular_file():
    assert_refused(os.devnull)


def test_c14_fifo_refused_before_opening(tmp_path):
    # Opening a FIFO with no writer blocks forever, so this runs in a subprocess with a
    # timeout: an implementation that opens before checking lstat fails by timing out.
    fifo = tmp_path / "pipe.csv"
    os.mkfifo(fifo)
    result = run_module([str(fifo)], timeout=30)
    assert result.returncode == 2
    assert len(result.stderr.strip().splitlines()) == 1


def test_c14_exactly_64_mib_is_accepted(tmp_path):
    head = log_text(steady(10)).encode("utf-8")
    pad_line = b" " * 1023 + b"\n"  # whitespace-only lines are skipped (C9)
    remaining = MIB_64 - len(head)
    full, rest = divmod(remaining, len(pad_line))
    tail = b" " * (rest - 1) + b"\n" if rest else b""
    path = tmp_path / "session.csv"
    path.write_bytes(head + pad_line * full + tail)
    assert path.stat().st_size == MIB_64
    log = measure.parse_log(str(path))
    assert len(log.rows) == 10
    assert log.bad_rows == 0


def test_c14_one_byte_over_64_mib_is_refused(tmp_path):
    path = write_log(tmp_path, steady(10))
    os.truncate(path, MIB_64 + 1)  # sparse: size without writing data
    assert path.stat().st_size == MIB_64 + 1
    assert_refused(path)


# ---- M1 + C8: bad rows -------------------------------------------------------------

GOOD_BEFORE = row(25.0, START_NS)
GOOD_AFTER = row(25.0, START_NS + 50 * MS)
FIELDS = len(COLUMNS)


@pytest.mark.parametrize(
    "bad_line",
    [
        ",".join(["1"] * (FIELDS - 1)),
        ",".join(["1"] * (FIELDS + 1)),
        row(25.0, START_NS + 25 * MS, cpu_load="abc"),
        row(25.0, START_NS + 25 * MS, cpu_load=""),
        row("nan", START_NS + 25 * MS),
        row("NaN", START_NS + 25 * MS),
        row("inf", START_NS + 25 * MS),
        row("-inf", START_NS + 25 * MS),
        row("Infinity", START_NS + 25 * MS),
        row(25.0, START_NS + 25 * MS, gpu_load="nan"),
        row(25.0, START_NS + 25 * MS, cpu_mhz="inf"),
        row(25.0, "nan"),
    ],
    ids=[
        "too_few_fields",
        "too_many_fields",
        "optional_column_not_a_float",
        "empty_field",
        "frametime_nan",
        "frametime_NaN",
        "frametime_inf",
        "frametime_minus_inf",
        "frametime_Infinity",
        "optional_column_nan",
        "optional_column_inf",
        "elapsed_nan",
    ],
)
def test_m1_bad_row_dropped_and_counted(tmp_path, bad_line):
    log = parse(tmp_path, [GOOD_BEFORE, bad_line, GOOD_AFTER])
    assert log.bad_rows == 1
    assert log.first_bad_line == 5
    assert [r["elapsed"] for r in log.rows] == [float(START_NS), float(START_NS + 50 * MS)]


def test_m1_first_bad_line_is_the_first_of_several(tmp_path):
    lines = [GOOD_BEFORE, row("nan", START_NS + MS), GOOD_AFTER, row("x", START_NS + 60 * MS)]
    log = parse(tmp_path, lines)
    assert log.bad_rows == 2
    assert log.first_bad_line == 5
    assert len(log.rows) == 2


@pytest.mark.parametrize("frametime", ["0", "0.0", "-0.0", "-5"])
def test_c8_frametime_zero_or_negative_is_bad(tmp_path, frametime):
    log = parse(tmp_path, [GOOD_BEFORE, row(frametime, START_NS + 25 * MS), GOOD_AFTER])
    assert log.bad_rows == 1
    assert log.first_bad_line == 5
    assert len(log.rows) == 2


def test_c8_negative_elapsed_is_bad(tmp_path):
    log = parse(tmp_path, [row(25.0, -1), row(25.0, 0), row(25.0, 25 * MS)])
    assert log.bad_rows == 1
    assert log.first_bad_line == 4
    assert [r["elapsed"] for r in log.rows] == [0.0, float(25 * MS)]


def test_c8_elapsed_going_backwards_is_bad_against_previous_non_bad_row(tmp_path):
    # elapsed: 1 s, 3 s, 2 s (bad: < 3 s), 2.5 s (bad: still < 3 s), 4 s (fine)
    elapsed = [1 * S, 3 * S, 2 * S, 2 * S + S // 2, 4 * S]
    log = parse(tmp_path, [row(25.0, e) for e in elapsed])
    assert log.bad_rows == 2
    assert log.first_bad_line == 6
    assert [r["elapsed"] for r in log.rows] == [float(1 * S), float(3 * S), float(4 * S)]


def test_c8_equal_elapsed_is_not_bad(tmp_path):
    log = parse(tmp_path, [row(25.0, S), row(25.0, S), row(25.0, 2 * S)])
    assert log.bad_rows == 0
    assert len(log.rows) == 3


# ---- C9: file hygiene --------------------------------------------------------------


def test_c9_blank_and_whitespace_lines_are_skipped_not_bad(tmp_path):
    lines = [GOOD_BEFORE, "", "   ", "\t", row(25.0, START_NS + 25 * MS), "", GOOD_AFTER, " "]
    log = parse(tmp_path, lines)
    assert log.bad_rows == 0
    assert log.first_bad_line is None
    assert len(log.rows) == 3


def test_c9_first_bad_line_counts_physical_file_lines(tmp_path):
    # line 4 good, line 5 blank, line 6 bad
    log = parse(tmp_path, [GOOD_BEFORE, "", row("nan", START_NS + MS), GOOD_AFTER])
    assert log.bad_rows == 1
    assert log.first_bad_line == 6


def test_c9_crlf_is_accepted(tmp_path):
    log = parse(tmp_path, steady(3), newline="\r\n")
    assert log.columns == COLUMNS
    assert log.system == EXPECTED_SYSTEM
    assert log.bad_rows == 0
    assert [r["elapsed"] for r in log.rows][-1] == float(START_NS + 50 * MS)


def test_c9_utf8_bom_on_line_1_is_removed(tmp_path):
    log = parse(tmp_path, steady(3), bom=True)
    assert log.system == EXPECTED_SYSTEM
    assert next(iter(log.system)) == "os"
    assert len(log.rows) == 3


def test_c9_bom_and_crlf_together(tmp_path):
    log = parse(tmp_path, steady(3), bom=True, newline="\r\n")
    assert log.system == EXPECTED_SYSTEM
    assert log.columns == COLUMNS
    assert len(log.rows) == 3


def test_c9_duplicate_column_names_raise(tmp_path):
    cols = ["fps", "frametime", "gpu_load", "elapsed", "fps"]
    path = tmp_path / "session.csv"
    path.write_text(log_text(["1,25,50,0,1"], columns=cols), encoding="utf-8")
    assert_refused(path)
