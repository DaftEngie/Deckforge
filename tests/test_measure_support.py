"""Fixture builders shared by the tests/test_measure_*.py files. Contains no tests.

Every log is written under pytest's tmp_path, in the MangoHud format from
docs/specs/measure.md: line 1 system names, line 2 system values, line 3 column names,
then one row per presented frame. Nothing here imports deckforge, so a missing
implementation shows up as an ImportError in the test files themselves.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SYSTEM_NAMES = "os,cpu,gpu,ram,kernel,driver,cpuscheduler"
SYSTEM_VALUES = (
    "Steam Runtime 4,AMD Custom APU 0932,AMD Custom GPU 0932 (RADV VANGOGH),15159840,"
    "6.18.50-valve2-1-neptune-618-gc7289a96b14d,,powersave"
)
COLUMNS = [
    "fps",
    "frametime",
    "cpu_load",
    "cpu_power",
    "gpu_load",
    "cpu_temp",
    "gpu_temp",
    "gpu_core_clock",
    "gpu_mem_clock",
    "gpu_vram_used",
    "gpu_power",
    "ram_used",
    "swap_used",
    "process_rss",
    "cpu_mhz",
    "elapsed",
]
# Values for the columns no rule reads, taken from the spec's example row.
FILLER = {
    "cpu_load": "80.4233",
    "cpu_power": "8.0826",
    "cpu_temp": "75",
    "gpu_temp": "66",
    "gpu_core_clock": "958",
    "gpu_mem_clock": "800",
    "gpu_vram_used": "0.926651",
    "gpu_power": "2",
    "ram_used": "8.68896",
    "swap_used": "0.375156",
    "process_rss": "0",
    "cpu_mhz": "3403",
}
START_NS = 10_423_837  # first elapsed value in the spec's example row
MS = 1_000_000  # nanoseconds per millisecond
S = 1_000_000_000  # nanoseconds per second


def _text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        return repr(value)
    return str(value)


def row(frametime, elapsed, gpu_load=89, columns=COLUMNS, **overrides) -> str:
    """One CSV data line. Values may be numbers or raw strings (e.g. "nan")."""
    if isinstance(frametime, int | float) and frametime > 0:
        fps = repr(round(1000 / frametime, 3))
    else:
        fps = "0"
    values = dict(FILLER, fps=fps, frametime=frametime, gpu_load=gpu_load, elapsed=elapsed)
    values.update(overrides)
    return ",".join(_text(values[c]) for c in columns)


def grid(frametimes, step_ns=25 * MS, start_ns=START_NS, gpu_load=89) -> list[str]:
    """Rows whose elapsed advances by a fixed step; frametime is set independently."""
    loads = gpu_load if isinstance(gpu_load, list) else [gpu_load] * len(frametimes)
    return [
        row(ft, start_ns + i * step_ns, load)
        for i, (ft, load) in enumerate(zip(frametimes, loads, strict=True))
    ]


LONG_STEP_NS = 500 * MS  # 300 rows -> 149.5 s: past SHORT_LOG_S, gaps under GAP_NS


def spread(frametimes, gpu_load=89) -> list[str]:
    """Same frame times, rows 500 ms apart so the log is >= 120 s for N >= 242.

    Elapsed spacing only feeds duration_s and stall detection; every fps metric and the
    verdict thresholds read frametime, so the tested numbers stay identical.
    """
    return grid(frametimes, LONG_STEP_NS, START_NS, gpu_load)


def front_loaded(frametimes, gpu_load=89) -> list[str]:
    """Same frame times, laid out so no 60 s window is slower than the whole log (F4),
    with no stalls, so playing time = duration_s >= 120 s (item 21).

    Frames at or below the mean frame time ("front") are spread evenly over [0, 120) s,
    under 1 s apart. Frames slower than the mean ("tail") all share elapsed = rel 120.0 s,
    which is then the last kept elapsed: every window must end at or before it (item 25),
    so no window holds a tail frame and every window average is at least the overall
    average. If every frame equals the mean, one is moved to the tail so the log reaches
    120 s.
    """
    mean = sum(frametimes) / len(frametimes)
    front = sorted(ft for ft in frametimes if ft <= mean)
    tail = sorted(ft for ft in frametimes if ft > mean)
    if not tail:
        tail = [front.pop()]
    assert len(front) > 120, "front frames must be under 1 s apart over 120 s"
    step = 120 * S // len(front)
    lines = [row(ft, START_NS + i * step, gpu_load) for i, ft in enumerate(front)]
    lines += [row(ft, START_NS + 120 * S, gpu_load) for ft in tail]
    return lines


def cumulative(frametimes, start_ns=START_NS, gpu_load=89) -> list[str]:
    """Realistic rows: each row's elapsed advances by its own frame time (whole ns)."""
    lines, elapsed = [], start_ns
    for i, ft in enumerate(frametimes):
        if i:
            elapsed += round(ft * MS)
        lines.append(row(ft, elapsed, gpu_load))
    return lines


def steady(n, frametime_ms=25.0, start_ns=START_NS, gpu_load=89) -> list[str]:
    """n frames of frametime_ms each, elapsed advancing by exactly that frame time."""
    return grid([frametime_ms] * n, round(frametime_ms * MS), start_ns, gpu_load)


def log_text(
    lines,
    columns=COLUMNS,
    system_names=SYSTEM_NAMES,
    system_values=SYSTEM_VALUES,
    newline="\n",
) -> str:
    header = [system_names, system_values, ",".join(columns)]
    return newline.join(header + list(lines)) + newline


def write_log(directory: Path, lines, name="session.csv", bom=False, newline="\n", **kw) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    data = log_text(lines, newline=newline, **kw).encode("utf-8")
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + data)
    return path


def sorted_markers(n, m5, m99, m999, fill):
    """Ascending frame times where the three percentile indices hold unique markers.

    fill = (below_m5, at_m5, between_m5_m99, at_m99, between_m99_m999, at_m999, above).
    """
    out = []
    for j in range(n):
        if j < m5:
            out.append(fill[0])
        elif j == m5:
            out.append(fill[1])
        elif j < m99:
            out.append(fill[2])
        elif j == m99:
            out.append(fill[3])
        elif j < m999:
            out.append(fill[4])
        elif j == m999:
            out.append(fill[5])
        else:
            out.append(fill[6])
    return out


def interleave(values):
    """Deterministic non-sorted order, so a missing sort is caught."""
    return values[1::2][::-1] + values[0::2]


def run_cli(measure, argv, capsys):
    """Call measure.main in-process; return (exit_code, stdout, stderr).

    argparse usage errors raise SystemExit(2); the spec allows either form of exit 2.
    """
    try:
        code = measure.main(argv)
    except SystemExit as exc:
        code = exc.code
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def run_module(args, timeout=60, env_extra=None):
    """Run `python -m deckforge.measure` in a subprocess with src on the path."""
    return run_python(["-m", "deckforge.measure", *args], timeout, env_extra)


def run_python(args, timeout=60, env_extra=None):
    """Run a fresh interpreter with src on the path; never raises on a non-zero exit."""
    env = dict(os.environ, PYTHONPATH=str(REPO / "src"), **(env_extra or {}))
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        cwd=str(REPO),
        check=False,
    )


def snapshot(folder: Path) -> dict:
    """Name -> (kind, bytes or link target, st_mtime_ns) for everything under folder."""
    result = {"<root>": ("dir", None, folder.lstat().st_mtime_ns)}
    for path in sorted(folder.rglob("*")):
        st = path.lstat()
        if path.is_symlink():
            entry = ("link", str(path.readlink()), st.st_mtime_ns)
        elif path.is_dir():
            entry = ("dir", None, st.st_mtime_ns)
        else:
            entry = ("file", path.read_bytes(), st.st_mtime_ns)
        result[str(path.relative_to(folder))] = entry
    return result


def parse_json(text: str) -> dict:
    return json.loads(text)
