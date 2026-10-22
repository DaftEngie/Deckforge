"""Read one MangoHud frame-time log and report how the session played.

Spec: docs/specs/measure.md (M1-M12 plus clarifier items 1-25, which win where they
differ). The target comes from decision 0002. This module only reads: it never creates,
changes or deletes a file (M12), and it adds no logging handlers (C15).

Run: ``PYTHONPATH=src python3 -m deckforge.measure [log] [--fg-multiplier N] [--json]``
"""

import argparse
import csv
import dataclasses
import json
import logging
import itertools
import math
import os
import stat
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---- Constants named by the spec ----------------------------------------------------

TARGET = {
    "gold_avg": 34.5,
    "gold_low": 33.0,
    "good_avg": 30.0,
    "good_low": 28.0,
    "real_low_floor": 14.0,
    "min_frames": 300,
}
ARTIFACT_MS = 10000
GAP_NS = 1_000_000_000
WINDOW_S = 60
WINDOW_STEP_S = 5
HITCH_MS = 100
GPU_BUSY_PCT = 90
GPU_SHARE_HI = 0.6
GPU_SHARE_LO = 0.2
GPU_MEAN_LO = 75
GPU_LOAD_MIN, GPU_LOAD_MAX = 0, 100  # item 20: gpu_load outside this range is a bad row
LOADING_GPU_MEAN = 50
SHORT_LOG_S = 120
SLOWER_THAN = (35, 30, 28)
MIN_FRAMETIME_MS = 0.1  # item 19 F2: no game frame takes under 0.1 ms
MAX_BAD_SHARE = 0.05  # item 19 F5: more bad rows than this share -> no verdict
MAX_JUMP_NS = 86_400_000_000_000  # item 20: a forward elapsed jump over 24 h is a bad row

# ---- Module-internal constants (values fixed by the spec, names are ours) -----------

MAX_LOG_BYTES = 64 * 1024 * 1024  # M1, C14: exactly 64 MiB is allowed
REQUIRED_COLUMNS = ("fps", "frametime", "elapsed")  # M1
SUMMARY_SUFFIX = "_summary.csv"  # M1, M11
NS_PER_S = 1_000_000_000
NS_PER_MS = 1_000_000
MAX_FG_MULTIPLIER = 4  # M5
P_MEDIAN, P_LOW_1, P_LOW_0_1 = 500, 990, 999  # C3: percentiles as k/1000

LIMIT_TEXT = {  # M6
    "gpu": "the graphics chip was the limit; graphics settings will raise fps",
    "not_gpu": (
        "the graphics chip had room to spare; the limit was likely the processor, or a frame cap"
    ),
    "mixed": "a mix",
    "unknown": "unknown (no gpu_load data in this log)",
}
WARNING_TEXT = {  # M8, M10
    "short_log": f"the log is shorter than {SHORT_LOG_S} s, so it may not be typical",
    "short_window": f"the log is shorter than {WINDOW_S} s; worst minute = whole session",
    "likely_loading_or_menus": (
        f"the graphics chip averaged under {LOADING_GPU_MEAN}% busy: "
        "likely loading screens or menus"
    ),
    "few_frames": f"fewer than {TARGET['min_frames']} frames, too few for a verdict",
    "bad_rows": "some rows were unreadable and were skipped",
    "too_many_bad_rows": (
        f"more than {MAX_BAD_SHARE * 100:g}% of rows were unreadable, too many for a verdict"
    ),
    "artifact_rows": "some rows had an impossible frame time (a MangoHud glitch) and were skipped",
    "no_gpu_data": "can't tell menus from gameplay without GPU load",
}
NOT_ENOUGH_DATA_TEXT = {  # C18: one reason per cause, in warning order
    "short_log": f"log is shorter than {SHORT_LOG_S:g} s",
    "likely_loading_or_menus": "the graphics chip was mostly idle, likely loading or menus",
    "few_frames": f"fewer than {TARGET['min_frames']} frames",
    "too_many_bad_rows": f"more than {MAX_BAD_SHARE * 100:g}% of rows were unreadable",
}
VERDICT_TEXT = {  # M9
    "gold": "GOLD: meets the gold target",
    "good_enough": "GOOD ENOUGH: meets the good-enough target",
    "fail": "FAIL: below the good-enough target",
    "not_enough_data": "NOT ENOUGH DATA: no verdict",
}


class MeasureError(Exception):
    """A log that cannot be measured. The CLI prints the message and exits 2 (M10)."""


@dataclasses.dataclass(frozen=True)
class MangoLog:
    """One parsed frame log (M1). ``rows`` holds every non-bad row, artifacts included (C17)."""

    path: str
    system: dict[str, str]
    columns: list[str]
    rows: list[dict[str, float]]
    bad_rows: int
    first_bad_line: int | None


# ---- M1: reading and parsing --------------------------------------------------------


def _read_text(path: str) -> str:
    """M1, C14, C17: lstat checks before opening, then read and decode as UTF-8.

    Refuses a missing path, anything but a regular file (links included), a file over
    MAX_LOG_BYTES, a ``_summary.csv`` name, and bytes that are not UTF-8.
    """
    if Path(path).name.endswith(SUMMARY_SUFFIX):
        raise MeasureError(
            f"{path!r} is a MangoHud summary file; pass the frame log instead "
            "(the same name without _summary)"
        )
    try:
        info = os.lstat(path)
    except OSError as exc:
        logger.debug("lstat failed for %r: %s", path, exc)
        raise MeasureError(f"cannot read {path!r}: {exc.strerror}") from exc
    _check_regular_and_size(path, info)
    data = _read_bytes(path)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MeasureError(f"{path!r} is not valid UTF-8 (byte {exc.start})") from exc
    return text.removeprefix("﻿")  # C9: BOM on line 1


def _check_regular_and_size(path: str, info: os.stat_result) -> None:
    """M1, C14: a regular file (by lstat, so links are refused) of at most 64 MiB."""
    if not stat.S_ISREG(info.st_mode):
        raise MeasureError(f"{path!r} is not a regular file (links are not followed)")
    if info.st_size > MAX_LOG_BYTES:
        raise MeasureError(f"{path!r} is larger than 64 MiB")


def _read_bytes(path: str) -> bytes:
    """Open read-only without following links or blocking, re-check, read (M1, M12)."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        logger.debug("open failed for %r: %s", path, exc)
        raise MeasureError(f"cannot open {path!r}: {exc.strerror}") from exc
    with os.fdopen(fd, "rb") as handle:
        _check_regular_and_size(path, os.fstat(handle.fileno()))
        return handle.read(MAX_LOG_BYTES + 1)


def _split_lines(text: str) -> list[str]:
    """Physical lines without their line ending; CRLF accepted (C9)."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [line.removesuffix("\r") for line in lines]


def _fields(line: str) -> list[str]:
    """One CSV line split into fields."""
    return next(csv.reader([line]))


def _parse_header(path: str, lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """M1, C9, item 19 F1: line 1 names + line 2 values -> system; line 3 -> columns."""
    if len(lines) < 3:
        raise MeasureError(f"{path!r} has fewer than 3 lines, so it is not a MangoHud log")
    try:
        names, values, column_fields = [_fields(line) for line in lines[:3]]
    except csv.Error as exc:
        logger.debug("csv rejected a header line (1-3) of %r: %s", path, exc)
        raise MeasureError(f"{path!r} header (lines 1-3) is unreadable: {exc}") from exc
    system = dict(zip(names, values, strict=True)) if len(names) == len(values) else {}
    columns = [name.strip() for name in column_fields]
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise MeasureError(f"{path!r} line 3 lacks required column(s): {', '.join(missing)}")
    if len(set(columns)) != len(columns):
        raise MeasureError(f"{path!r} line 3 has duplicate column names")
    return system, columns


def _parse_row(line: str, columns: list[str]) -> dict[str, float] | None:
    """M1: one data row as floats, or None when the field count or a value is bad."""
    fields = _fields(line)
    if len(fields) != len(columns):
        return None
    values = {}
    for name, field in zip(columns, fields, strict=True):
        try:
            value = float(field)
        except ValueError:
            return None
        if not math.isfinite(value):
            return None
        values[name] = value
    return values


def _fails_row_checks(values: dict[str, float] | None) -> bool:
    """M1, C8, F2, item 20: unreadable, frametime < MIN_FRAMETIME_MS, elapsed < 0, or
    gpu_load (when present) outside [GPU_LOAD_MIN, GPU_LOAD_MAX]. Needs no other row.
    """
    if values is None or values["frametime"] < MIN_FRAMETIME_MS or values["elapsed"] < 0:
        return True
    return "gpu_load" in values and not GPU_LOAD_MIN <= values["gpu_load"] <= GPU_LOAD_MAX


def _is_bad(
    values: dict[str, float],
    previous_elapsed: float | None,
    next_elapsed: float | None,
) -> bool:
    """C8, item 20, item 22 for a row that passes the row checks: elapsed going back or
    jumping more than MAX_JUMP_NS past the previous non-bad row, or a lone forward spike
    (above the next data row, which is itself not below the previous non-bad row).
    Item 24: with no previous non-bad row, a row is bad if it is above the next data row.
    """
    if previous_elapsed is None:
        return next_elapsed is not None and values["elapsed"] > next_elapsed
    step = values["elapsed"] - previous_elapsed
    if step < 0 or step > MAX_JUMP_NS:
        return True
    return next_elapsed is not None and values["elapsed"] > next_elapsed >= previous_elapsed


def parse_log(path) -> MangoLog:
    """M1: parse one MangoHud frame log. Raises MeasureError for a log it cannot read."""
    path = str(path)
    lines = _split_lines(_read_text(path))
    system, columns = _parse_header(path, lines)
    data: list[tuple[int, dict[str, float] | None]] = []
    for number, line in enumerate(lines[3:], start=4):
        if not line.strip():  # C9: blank lines are skipped, not bad
            continue
        try:
            values = _parse_row(line, columns)
        except csv.Error as exc:  # item 19 F1: a row the csv module rejects is a bad row
            logger.debug("csv rejected %r line %d: %s", path, number, exc)
            values = None
        data.append((number, None if _fails_row_checks(values) else values))
    # Item 22: elapsed of the next row passing the row checks, filled in one backward pass.
    next_elapsed: list[float | None] = [None] * len(data)
    for index in range(len(data) - 2, -1, -1):
        following = data[index + 1][1]
        next_elapsed[index] = next_elapsed[index + 1] if following is None else following["elapsed"]
    rows: list[dict[str, float]] = []
    bad_rows = 0
    first_bad_line = None
    for (number, values), after in zip(data, next_elapsed, strict=True):
        previous = rows[-1]["elapsed"] if rows else None
        if values is None or _is_bad(values, previous, after):
            bad_rows += 1
            if first_bad_line is None:
                first_bad_line = number  # C17: physical line, blanks included
            continue
        rows.append(values)
    return MangoLog(path, system, columns, rows, bad_rows, first_bad_line)


# ---- M2, M3: artifacts and stalls ---------------------------------------------------


def _split_artifacts(rows: list[dict[str, float]]) -> tuple[list[dict[str, float]], int]:
    """C6 (replaces M2): return (kept rows, artifact count).

    A row is an artifact when frametime > ARTIFACT_MS and frametime > 2x the gap in ms
    since the previous non-bad row (kept or artifact). The first row is an artifact when
    frametime > ARTIFACT_MS.
    """
    kept = []
    artifacts = 0
    previous = None
    for values in rows:
        frametime = values["frametime"]
        is_artifact = frametime > ARTIFACT_MS
        if is_artifact and previous is not None:
            gap_ms = (values["elapsed"] - previous) / NS_PER_MS
            is_artifact = frametime > 2 * gap_ms
        if is_artifact:
            artifacts += 1
        else:
            kept.append(values)
        previous = values["elapsed"]
    return kept, artifacts


def _stalls(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    """M3, C7, C17: elapsed gaps > GAP_NS between consecutive non-bad rows.

    ``at_s`` is the earlier row's time from the first non-bad row.
    """
    if not rows:
        return []
    origin = rows[0]["elapsed"]
    stalls = []
    for earlier, later in zip(rows, rows[1:], strict=False):
        gap = later["elapsed"] - earlier["elapsed"]
        if gap > GAP_NS:
            stalls.append(
                {
                    "at_s": round((earlier["elapsed"] - origin) / NS_PER_S, 1),
                    "duration_s": round(gap / NS_PER_S, 1),
                }
            )
    return stalls


def _stall_s_between_kept(kept: list[dict[str, float]]) -> float:
    """Items 21, 22: unrounded seconds of gaps > GAP_NS between consecutive kept rows.

    Artifact and bad rows between two kept rows are ignored.
    """
    total = 0
    for earlier, later in zip(kept, kept[1:], strict=False):
        gap = later["elapsed"] - earlier["elapsed"]
        if gap > GAP_NS:
            total += gap
    return total / NS_PER_S


# ---- M4: smoothness metrics ---------------------------------------------------------


def _percentile(sorted_ms: list[float], k: int) -> float:
    """C3: nearest-rank P(k/1000) on an ascending list, integer index only."""
    return sorted_ms[(k * len(sorted_ms) + 999) // 1000 - 1]


def _avg_fps(frametimes: list[float]) -> float:
    """M4: 1000 * N / sum(F)."""
    return 1000 * len(frametimes) / math.fsum(frametimes)


def _low_1pct_fps(sorted_ms: list[float]) -> float:
    """M4: 1000 / P(0.99)."""
    return 1000 / _percentile(sorted_ms, P_LOW_1)


def _slower_than(frametimes: list[float]) -> dict[str, float]:
    """M4, C10: share of frames slower than x fps (frame time > 1000/x), per SLOWER_THAN."""
    n = len(frametimes)
    return {
        str(fps): round(sum(1 for ft in frametimes if ft > 1000 / fps) / n, 3)
        for fps in SLOWER_THAN
    }


# ---- M6: what limited it ------------------------------------------------------------


def _limit(kept: list[dict[str, float]], columns: list[str]) -> tuple[str, float | None]:
    """M6: return (limit, unrounded gpu busy share or None)."""
    if "gpu_load" not in columns or not kept:
        return "unknown", None
    loads = [values["gpu_load"] for values in kept]
    share = sum(1 for load in loads if load >= GPU_BUSY_PCT) / len(loads)
    mean = math.fsum(loads) / len(loads)
    if share >= GPU_SHARE_HI:
        return "gpu", share
    if share < GPU_SHARE_LO and mean < GPU_MEAN_LO:
        return "not_gpu", share
    return "mixed", share


def _gpu_mean(kept: list[dict[str, float]], columns: list[str]) -> float | None:
    """Mean gpu_load over kept rows, or None without the column or frames (M8)."""
    if "gpu_load" not in columns or not kept:
        return None
    return math.fsum(values["gpu_load"] for values in kept) / len(kept)


# ---- M7: worst minute ---------------------------------------------------------------


def _worst_window(kept: list[dict[str, float]]) -> tuple[dict[str, float], bool, float]:
    """M7, C10, item 25: return (worst window, short_window flag, its unrounded avg fps).

    A window may start at the elapsed of every kept row while start + WINDOW_S <= the
    last kept elapsed; it covers [start, start + WINDOW_S) over kept rows. The lowest
    unrounded avg (count * 1000 / window sum) wins, ties to the earliest start. With no
    candidate the whole session is one window starting at 0 (short_window). Linear time:
    two pointers over prefix sums of frame times; the 1% low is computed only for the
    chosen window. WINDOW_STEP_S is no longer used.
    """
    origin = kept[0]["elapsed"]
    rel = [values["elapsed"] - origin for values in kept]
    frametimes = [values["frametime"] for values in kept]
    duration = rel[-1]
    width = WINDOW_S * NS_PER_S
    if duration < width:
        return _window_result(0, frametimes), True, _avg_fps(frametimes)
    prefix = [0.0, *itertools.accumulate(frametimes)]
    best = None
    hi = 0
    for lo, start in enumerate(rel):
        if start + width > duration:
            break
        if lo > 0 and rel[lo - 1] == start:
            continue  # same elapsed as the row before: the same window, already scored
        while rel[hi] < start + width:  # stops by the last row: start + width <= rel[-1]
            hi += 1
        avg = 1000 * (hi - lo) / (prefix[hi] - prefix[lo])
        if best is None or avg < best[0]:
            best = (avg, start, lo, hi)
    _, start, lo, hi = best
    window = frametimes[lo:hi]
    return _window_result(start, window), False, _avg_fps(window)


def _window_result(start_ns: int, frametimes: list[float]) -> dict[str, float]:
    """The rounded worst_window dict (C4)."""
    return {
        "start_s": round(start_ns / NS_PER_S, 1),
        "avg_fps": round(_avg_fps(frametimes), 1),
        "low_1pct_fps": round(_low_1pct_fps(sorted(frametimes)), 1),
    }


# ---- M8, M9: warnings and verdict ---------------------------------------------------


def _warnings(
    playing_s: float | None,
    short_window: bool,
    gpu_mean: float | None,
    frames: int,
    bad_rows: int,
    data_rows: int,
    artifact_rows: int,
    has_gpu_data: bool,
) -> list[str]:
    """M8, item 19 F3, F5: each warning that applies, in the spec's order.

    ``playing_s`` is duration_s minus gaps between consecutive kept rows (items 21, 22).
    ``data_rows`` is bad plus non-bad data rows, blank lines excluded.
    """
    checks = [
        ("short_log", playing_s is not None and playing_s < SHORT_LOG_S),
        ("short_window", short_window),
        ("likely_loading_or_menus", gpu_mean is not None and gpu_mean < LOADING_GPU_MEAN),
        ("few_frames", frames < TARGET["min_frames"]),
        ("bad_rows", bad_rows > 0),
        ("too_many_bad_rows", data_rows > 0 and bad_rows / data_rows > MAX_BAD_SHARE),
        ("artifact_rows", artifact_rows > 0),
        ("no_gpu_data", not has_gpu_data),
    ]
    return [name for name, applies in checks if applies]


def _reason_number(value: float, threshold: float) -> str:
    """C18: the report's round(x, 1), or round-down if that would reach the threshold."""
    shown = round(value, 1)
    if shown >= threshold:
        shown = math.floor(value * 10) / 10
    return f"{shown:.1f}"


def _verdict(
    warnings: list[str],
    avg: float | None,
    low: float | None,
    real_low: float | None,
    worst_avg: float | None,
) -> tuple[str, list[str]]:
    """M9, C1, C11, C18, item 19 F4: verdict and reasons from unrounded values.

    Any unrepresentative-log warning (N = 0 always has few_frames) -> not_enough_data,
    with one reason per cause.
    """
    causes = [NOT_ENOUGH_DATA_TEXT[name] for name in warnings if name in NOT_ENOUGH_DATA_TEXT]
    if causes:
        return "not_enough_data", causes
    floor_ok = real_low >= TARGET["real_low_floor"]
    gold_avg, good_avg = TARGET["gold_avg"], TARGET["good_avg"]
    if avg >= gold_avg and low >= TARGET["gold_low"] and floor_ok and worst_avg >= gold_avg:
        return "gold", []
    if avg >= good_avg and low >= TARGET["good_low"] and floor_ok and worst_avg >= good_avg:
        return "good_enough", []
    tests = [
        (avg, TARGET["good_avg"], "average {} fps is below {:g}"),
        (low, TARGET["good_low"], "1% low {} fps is below {:g}"),
        (real_low, TARGET["real_low_floor"], "real-frame 1% low {} fps is below {:g}"),
        (worst_avg, good_avg, "worst minute averaged {} fps, below {:g}"),
    ]
    reasons = [text.format(_reason_number(v, t), t) for v, t, text in tests if v < t]
    return "fail", reasons


# ---- analyze ------------------------------------------------------------------------


def _check_fg_multiplier(fg_multiplier) -> None:
    """M5, C12: an int (not a bool) from 1 to MAX_FG_MULTIPLIER."""
    is_int = isinstance(fg_multiplier, int) and not isinstance(fg_multiplier, bool)
    if not is_int or not 1 <= fg_multiplier <= MAX_FG_MULTIPLIER:
        raise MeasureError(
            f"--fg-multiplier must be a whole number from 1 to {MAX_FG_MULTIPLIER}, "
            f"got {fg_multiplier!r}"
        )


def _frame_metrics(kept: list[dict[str, float]], fg_multiplier: int) -> dict:
    """M4, M5, M7 on N >= 1 kept frames; unrounded values used by the verdict included."""
    frametimes = [values["frametime"] for values in kept]
    ordered = sorted(frametimes)
    avg = _avg_fps(frametimes)
    low = _low_1pct_fps(ordered)
    worst, short_window, worst_avg = _worst_window(kept)
    return {
        "avg": avg,
        "low": low,
        "real_low": low / fg_multiplier,
        "worst_avg": worst_avg,
        "duration_s": (kept[-1]["elapsed"] - kept[0]["elapsed"]) / NS_PER_S,
        "short_window": short_window,
        "report": {
            "avg_fps": round(avg, 1),
            "median_fps": round(1000 / _percentile(ordered, P_MEDIAN), 1),
            "low_1pct_fps": round(low, 1),
            "low_0_1pct_fps": round(1000 / _percentile(ordered, P_LOW_0_1), 1),
            "real_avg_fps": round(avg / fg_multiplier, 1),
            "real_low_1pct_fps": round(low / fg_multiplier, 1),
            "slower_than": _slower_than(frametimes),
            "worst_window": worst,
        },
    }


def _empty_metrics() -> dict:
    """C2: N = 0, so no percentile or division is attempted."""
    return {
        "avg": None,
        "low": None,
        "real_low": None,
        "worst_avg": None,
        "duration_s": None,
        "short_window": False,
        "report": {
            "avg_fps": None,
            "median_fps": None,
            "low_1pct_fps": None,
            "low_0_1pct_fps": None,
            "real_avg_fps": None,
            "real_low_1pct_fps": None,
            "slower_than": {},
            "worst_window": None,
        },
    }


def analyze(log: MangoLog, *, fg_multiplier: int = 1) -> dict:
    """M2-M9, C4, C5: the final, rounded report dict for one parsed log."""
    _check_fg_multiplier(fg_multiplier)
    kept, artifact_rows = _split_artifacts(log.rows)
    m = _frame_metrics(kept, fg_multiplier) if kept else _empty_metrics()
    limit, share = _limit(kept, log.columns)
    playing_s = None
    if m["duration_s"] is not None:
        playing_s = m["duration_s"] - _stall_s_between_kept(kept)
    warnings = _warnings(
        playing_s,
        m["short_window"],
        _gpu_mean(kept, log.columns),
        len(kept),
        log.bad_rows,
        log.bad_rows + len(log.rows),
        artifact_rows,
        "gpu_load" in log.columns,
    )
    verdict, reasons = _verdict(warnings, m["avg"], m["low"], m["real_low"], m["worst_avg"])
    duration_s = None if m["duration_s"] is None else round(m["duration_s"], 1)
    return {
        **m["report"],
        "artifact_rows": artifact_rows,
        "bad_rows": log.bad_rows,
        "duration_s": duration_s,
        "fg_multiplier": fg_multiplier,
        "file": Path(log.path).name,
        "first_bad_line": log.first_bad_line,
        "frames": len(kept),
        "gpu_busy_share": None if share is None else round(share, 3),
        "hitches": sum(1 for values in kept if values["frametime"] > HITCH_MS),
        "limit": limit,
        "real_is_estimate": fg_multiplier > 1,
        "reasons": reasons,
        "stalls": _stalls(log.rows),
        "system": dict(log.system),
        "verdict": verdict,
        "warnings": warnings,
    }


# ---- M10: text report ---------------------------------------------------------------


def _fps(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f} fps"


def format_text(report: dict) -> str:
    """M10: a short plain-English report; item 21: non-UTF-8 name bytes as escapes."""
    name = os.fsencode(report["file"]).decode("utf-8", "backslashreplace")
    lines = [f"Log: {name}"]
    duration = report["duration_s"]
    lines.append(
        f"Duration: {'n/a' if duration is None else f'{duration:.1f} s'}, {report['frames']} frames"
    )
    lines.append(
        f"On screen: average {_fps(report['avg_fps'])}, median {_fps(report['median_fps'])}, "
        f"1% low {_fps(report['low_1pct_fps'])}, 0.1% low {_fps(report['low_0_1pct_fps'])}"
    )
    real = (
        f"Real frames: average {_fps(report['real_avg_fps'])}, "
        f"1% low {_fps(report['real_low_1pct_fps'])}"
    )
    if report["real_is_estimate"]:
        real += f" (estimated, assuming each real frame is shown {report['fg_multiplier']} times)"
    lines.append(real)
    lines.append(f"Limit: {LIMIT_TEXT[report['limit']]}")
    worst = report["worst_window"]
    if worst is not None:
        lines.append(
            f"Worst minute: starting at {worst['start_s']:.1f} s, average "
            f"{_fps(worst['avg_fps'])}, 1% low {_fps(worst['low_1pct_fps'])}"
        )
    lines.append(
        f"Stalls over 1 s: {len(report['stalls'])}; hitches over 100 ms: {report['hitches']}"
    )
    for name in report["warnings"]:
        lines.append(f"Warning: {WARNING_TEXT[name]}")
    lines.append(f"Verdict: {VERDICT_TEXT[report['verdict']]}")
    lines.extend(f"  - {reason}" for reason in report["reasons"])
    return "\n".join(lines) + "\n"


# ---- M11: picking the log -----------------------------------------------------------


def _candidate_key(entry: os.DirEntry) -> tuple[int, str] | None:
    """M11, C13: (st_mtime_ns, name) for a lowercase .csv regular file (by lstat)."""
    name = entry.name
    if not name.endswith(".csv") or name.endswith(SUMMARY_SUFFIX):
        return None
    info = entry.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        return None
    return info.st_mtime_ns, name


def newest_log(logs_dir: str) -> str:
    """M11, C13: newest frame log in logs_dir; ties on mtime_ns go to the last name.

    The folder itself may be a link and is followed; links inside it are skipped.
    """
    try:
        with os.scandir(logs_dir) as entries:
            candidates = [key for entry in entries if (key := _candidate_key(entry))]
    except OSError as exc:
        logger.debug("cannot list logs folder %r: %s", logs_dir, exc)
        raise MeasureError(f"cannot list logs folder {logs_dir!r}: {exc.strerror}") from exc
    if not candidates:
        raise MeasureError(f"no frame log (.csv) found in {logs_dir!r}")
    _, name = max(candidates)
    return str(Path(logs_dir) / name)


# ---- CLI ----------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deckforge.measure",
        description="Report how a session played, from its MangoHud frame log.",
    )
    parser.add_argument("log", nargs="?", help="frame log; default: newest in --logs-dir")
    parser.add_argument("--logs-dir", help="folder of logs (default: <home>/deckforge/logs)")
    parser.add_argument("--home", default=str(Path("~").expanduser()), help=argparse.SUPPRESS)
    parser.add_argument(
        "--fg-multiplier",
        type=int,
        default=1,
        help="frames shown per real frame with frame generation on (1-4, default 1)",
    )
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    """M10-M12: print the report; 0 on any verdict, 2 on MeasureError (one stderr line)."""
    args = _build_parser().parse_args(argv)
    try:
        _check_fg_multiplier(args.fg_multiplier)
        if args.log is not None:  # C12: a positional log wins over --logs-dir
            path = args.log
        else:
            logs_dir = args.logs_dir or str(Path(args.home) / "deckforge" / "logs")
            path = newest_log(logs_dir)
        report = analyze(parse_log(path), fg_multiplier=args.fg_multiplier)
    except MeasureError as exc:
        message = " ".join(str(exc).splitlines())
        print(f"deckforge.measure: {message}", file=sys.stderr)
        return 2
    if args.json:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    else:
        sys.stdout.write(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
