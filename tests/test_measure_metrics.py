"""deckforge.measure.analyze metrics: spec docs/specs/measure.md, M2-M7 + clarifiers 2-4, 6, 7, 10.

CONTRACTS (written from the spec before any implementation exists)

analyze(log, *, fg_multiplier=1) -> dict
  Preconditions:
    - log is a MangoLog from parse_log (bad rows already removed).
    - fg_multiplier is an int (not a bool) in 1..4, else MeasureError.            [M5, C12]
  Postconditions (all on the final, rounded dict; decisions use unrounded values) [C4]:
    - artifact: frametime > ARTIFACT_MS and frametime > 2 x (elapsed gap in ms since the
      previous non-bad row); the first non-bad row is an artifact if frametime >
      ARTIFACT_MS. Artifacts count in artifact_rows and are excluded from every metric.
                                                                                 [C6]
    - stalls: every elapsed gap > GAP_NS between consecutive non-bad rows (kept or
      artifact), as {"at_s", "duration_s"}; at_s from the first KEPT row.        [M3, C7]
    - hitches: kept frames with frametime > HITCH_MS.                            [M3]
    - frames = N kept; duration_s = (last kept - first kept elapsed) / 1e9.       [M4, C7]
    - avg_fps = 1000 N / sum(F); P(k/1000) = sorted(F)[(k N + 999) // 1000 - 1];
      median_fps = 1000/P(.5); low_1pct_fps = 1000/P(.99); low_0_1pct_fps = 1000/P(.999).
                                                                                 [M4, C3]
    - slower_than = {"35","30","28"} -> share of F > 1000/x.                     [M4, C10]
    - real_avg_fps = avg_fps / m; real_low_1pct_fps = low_1pct_fps / m (from unrounded);
      real_is_estimate = m > 1.                                                  [M5, C4]
    - limit / gpu_busy_share from kept rows' gpu_load (>= 90 busy; >= 0.6 gpu;
      < 0.2 and mean < 75 not_gpu; else mixed; no column -> unknown, share None).  [M6]
    - worst_window: lowest unrounded avg over [start, start + 60) windows starting at
      kept-relative 0, 5, 10 ... while start + 60 <= duration_s; empty windows skipped;
      earliest wins ties; whole session (start 0) if duration_s < 60.            [M7, C10]
    - N = 0: frames 0; fps fields, real_avg/low, duration_s, gpu_busy_share and
      worst_window None; slower_than {}; limit "unknown"; verdict not_enough_data.  [C2]
    - Rounding: fps, duration_s, stall times, start_s -> round(x, 1); shares -> round(x, 3).
  Invariants: analyze never mutates the log and never touches the disk.
"""

import pytest
from test_measure_support import (
    COLUMNS,
    MS,
    S,
    START_NS,
    grid,
    interleave,
    row,
    sorted_markers,
    steady,
    write_log,
)

from deckforge import measure

ARTIFACT = 22_000_000.0  # the ~2.2e7 wall-clock value seen in Fede's logs


def report(tmp_path, lines, fg=1, **kw):
    log = measure.parse_log(str(write_log(tmp_path, lines, **kw)))
    return measure.analyze(log, fg_multiplier=fg)


# ---- constants ---------------------------------------------------------------------


def test_m0_target_and_named_constants_match_spec():
    assert measure.TARGET == {
        "gold_avg": 34.5,
        "gold_low": 33.0,
        "good_avg": 30.0,
        "good_low": 28.0,
        "real_low_floor": 14.0,
        "min_frames": 300,
    }
    assert measure.ARTIFACT_MS == 10000
    assert measure.GAP_NS == 1_000_000_000
    assert measure.WINDOW_S == 60


def test_c10_new_named_constants_match_spec():
    assert measure.WINDOW_STEP_S == 5
    assert measure.HITCH_MS == 100
    assert measure.GPU_BUSY_PCT == 90
    assert measure.GPU_SHARE_HI == 0.6
    assert measure.GPU_SHARE_LO == 0.2
    assert measure.GPU_MEAN_LO == 75
    assert measure.LOADING_GPU_MEAN == 50
    assert measure.SHORT_LOG_S == 120
    assert tuple(measure.SLOWER_THAN) == (35, 30, 28)


# ---- C3 / M4: percentiles ----------------------------------------------------------

# Markers: P(.5) -> 12.5 ms (80.0 fps), P(.99) -> 20 ms (50.0), P(.999) -> 40 ms (25.0).
# Neighbours of each index hold different values, so an off-by-one shows.
MARKERS = (10.0, 12.5, 15.0, 20.0, 25.0, 40.0, 50.0)


@pytest.mark.parametrize(
    ("n", "m5", "m99", "m999"),
    [
        # (k*N + 999) // 1000 - 1, worked by hand:
        (100, 49, 98, 99),  # 50999//1000-1, 99999//1000-1, 100899//1000-1
        (1000, 499, 989, 998),  # 500999//1000-1, 990999//1000-1, 999999//1000-1
        (1001, 500, 990, 999),  # 501499//1000-1, 991989//1000-1, 1000998//1000-1
    ],
)
def test_c3_percentile_index_is_integer_nearest_rank(tmp_path, n, m5, m99, m999):
    frametimes = interleave(sorted_markers(n, m5, m99, m999, MARKERS))
    r = report(tmp_path, grid(frametimes))
    assert r["frames"] == n
    assert r["median_fps"] == 80.0
    assert r["low_1pct_fps"] == 50.0
    assert r["low_0_1pct_fps"] == 25.0


def test_c3_single_frame_is_every_percentile(tmp_path):
    r = report(tmp_path, [row(25.0, START_NS)])
    assert r["frames"] == 1
    assert r["avg_fps"] == 40.0
    assert r["median_fps"] == 40.0
    assert r["low_1pct_fps"] == 40.0
    assert r["low_0_1pct_fps"] == 40.0
    assert r["duration_s"] == 0.0


# ---- M4: averages, duration, shares, rounding --------------------------------------


def test_m4_avg_fps_is_frames_over_total_time_not_mean_of_fps(tmp_path):
    # 3000 / (20 + 30 + 50) = 30.0; the mean of per-frame fps would be 34.4.
    r = report(tmp_path, grid([20.0, 30.0, 50.0]))
    assert r["frames"] == 3
    assert r["avg_fps"] == 30.0


def test_m4_duration_is_last_minus_first_elapsed(tmp_path):
    r = report(tmp_path, steady(401, 25.0, start_ns=3 * S))  # 400 x 25 ms = 10 s
    assert r["duration_s"] == 10.0


def test_m4_slower_than_shares(tmp_path):
    # 1000/35 = 28.57, 1000/30 = 33.33, 1000/28 = 35.71
    frametimes = [20.0] * 4 + [30.0] * 2 + [34.0] + [40.0] * 3
    r = report(tmp_path, grid(interleave(frametimes)))
    assert r["slower_than"] == {"35": 0.6, "30": 0.4, "28": 0.3}


def test_m4_slower_than_rounds_to_3_decimals(tmp_path):
    r = report(tmp_path, grid([20.0] * 4 + [40.0] * 3))  # 3/7 = 0.42857
    assert r["slower_than"] == {"35": 0.429, "30": 0.429, "28": 0.429}


def test_c4_fps_fields_rounded_to_1_decimal(tmp_path):
    # N=1000; sum = 499*15 + 16 + 489*20 + 22 + 8*30 + 35 + 42 = 17620 ms
    fill = (15.0, 16.0, 20.0, 22.0, 30.0, 35.0, 42.0)
    r = report(tmp_path, grid(interleave(sorted_markers(1000, 499, 989, 998, fill))))
    assert r["avg_fps"] == 56.8  # 1e6 / 17620 = 56.7537
    assert r["median_fps"] == 62.5  # 1000 / 16
    assert r["low_1pct_fps"] == 45.5  # 1000 / 22 = 45.4545
    assert r["low_0_1pct_fps"] == 28.6  # 1000 / 35 = 28.5714


# ---- M2 / C6: artifact rows --------------------------------------------------------


def test_m2_artifact_row_excluded(tmp_path):
    frametimes = [25.0] * 401
    frametimes[200] = ARTIFACT  # elapsed still advances 25 ms
    r = report(tmp_path, grid(frametimes))
    assert r["artifact_rows"] == 1
    assert r["frames"] == 400
    assert r["avg_fps"] == 40.0
    assert r["low_0_1pct_fps"] == 40.0
    assert r["hitches"] == 0
    assert r["stalls"] == []


def test_m2_artifact_excluded_from_gpu_share_and_slower_than(tmp_path):
    lines = grid([25.0] * 9, gpu_load=10)
    lines.append(row(ARTIFACT, START_NS + 9 * 25 * MS, gpu_load=100))
    r = report(tmp_path, lines)
    assert r["frames"] == 9
    assert r["artifact_rows"] == 1
    assert r["gpu_busy_share"] == 0.0
    assert r["limit"] == "not_gpu"
    assert r["slower_than"] == {"35": 0.0, "30": 0.0, "28": 0.0}


def test_c6_artifact_after_real_gap(tmp_path):
    # 10 s of play, a real 5 s stall, then a 2.2e7 row: still an artifact, since
    # 2.2e7 ms > 2 x 5000 ms. The stall itself is still reported.
    lines = steady(401)  # rel 0 .. 10 s
    lines.append(row(ARTIFACT, START_NS + 15 * S))
    lines += steady(400, start_ns=START_NS + 15 * S + 25 * MS)
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 1
    assert r["frames"] == 801
    assert r["hitches"] == 0
    assert r["avg_fps"] == 40.0
    assert r["stalls"] == [{"at_s": 10.0, "duration_s": 5.0}]


def test_c6_long_real_frame_after_real_gap_is_kept(tmp_path):
    # 30000 ms after a 30 s gap is a real frame: not > 2 x 30000.
    lines = steady(401)
    lines.append(row(30000.0, START_NS + 40 * S))
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 0
    assert r["frames"] == 402
    assert r["hitches"] == 1
    assert r["stalls"] == [{"at_s": 10.0, "duration_s": 30.0}]


def test_c6_artifact_ms_threshold_is_strict(tmp_path):
    lines = steady(3)
    lines.append(row(10000.0, START_NS + 75 * MS))  # not > 10000: kept
    lines.append(row(10000.001, START_NS + 100 * MS))  # > 10000 and > 2 x 25: artifact
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 1
    assert r["frames"] == 4
    assert r["hitches"] == 1


def test_c6_twice_the_gap_boundary_is_strict(tmp_path):
    lines = steady(2)  # rel 0, 25 ms
    lines.append(row(12000.0, START_NS + 25 * MS + 6 * S))  # == 2 x 6000: kept
    lines.append(row(12000.5, START_NS + 25 * MS + 12 * S))  # > 2 x 6000: artifact
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 1
    assert r["frames"] == 3
    assert r["hitches"] == 1


def test_c6_first_non_bad_row_is_artifact_when_over_artifact_ms(tmp_path):
    lines = [row("nan", START_NS - MS), row(ARTIFACT, START_NS)]
    lines += steady(300, start_ns=START_NS + 25 * MS)
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 1
    assert r["frames"] == 300
    assert r["avg_fps"] == 40.0


def test_c6_first_row_exactly_artifact_ms_is_kept(tmp_path):
    lines = [row(10000.0, START_NS)] + steady(10, start_ns=START_NS + 25 * MS)
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 0
    assert r["frames"] == 11
    assert r["hitches"] == 1


def test_c6_gap_is_measured_from_previous_non_bad_row_not_bad_row(tmp_path):
    # kept at 0 s; bad row at 19.9 s; 15000 ms row at 20 s. Gap from the previous
    # non-bad row is 20000 ms, so 15000 is a real frame (kept, a hitch).
    lines = [
        row(25.0, START_NS),
        row(25.0, START_NS + 19_900 * MS, gpu_load="nan"),
        row(15000.0, START_NS + 20 * S),
    ]
    r = report(tmp_path, lines)
    assert r["bad_rows"] == 1
    assert r["artifact_rows"] == 0
    assert r["frames"] == 2
    assert r["hitches"] == 1


def test_c6_gap_is_measured_from_previous_artifact_row(tmp_path):
    # kept at 0 s; artifact at 20 s; 15000 ms row 100 ms after the artifact.
    # 15000 > 2 x 100, so it is an artifact too (measuring from the kept row would keep it).
    lines = [
        row(25.0, START_NS),
        row(ARTIFACT, START_NS + 20 * S),
        row(15000.0, START_NS + 20 * S + 100 * MS),
    ]
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 2
    assert r["frames"] == 1


# ---- M3 / C7: stalls and hitches ---------------------------------------------------


def test_m3_stall_reported_from_first_row(tmp_path):
    lines = steady(401, start_ns=3_300 * MS)  # rel 0 .. 10 s; absolute 3.3 .. 13.3 s
    lines += steady(10, start_ns=3_300 * MS + 12_500 * MS)  # 2.5 s gap
    r = report(tmp_path, lines)
    assert r["stalls"] == [{"at_s": 10.0, "duration_s": 2.5}]


def test_m3_gap_of_exactly_gap_ns_is_not_a_stall(tmp_path):
    lines = [row(25.0, START_NS), row(25.0, START_NS + S), row(25.0, START_NS + 2 * S + 1)]
    r = report(tmp_path, lines)
    assert r["stalls"] == [{"at_s": 1.0, "duration_s": 1.0}]


def test_m3_hitches_count_kept_frames_over_100_ms(tmp_path):
    r = report(tmp_path, grid([25.0, 100.0, 100.001, 250.0, 25.0]))
    assert r["hitches"] == 2


def test_c7_stall_ignores_bad_rows(tmp_path):
    lines = [
        row(25.0, START_NS),
        row(25.0, START_NS + 900 * MS, gpu_load="nan"),
        row(25.0, START_NS + 1800 * MS),
    ]
    r = report(tmp_path, lines)
    assert r["bad_rows"] == 1
    assert r["stalls"] == [{"at_s": 0.0, "duration_s": 1.8}]


def test_c7_times_measured_from_first_kept_row_not_first_artifact(tmp_path):
    # artifact at 0 s; kept 0.5 .. 10.5 s; 2 s stall; kept 12.5 .. 22.5 s
    lines = [row(ARTIFACT, 0)]
    lines += steady(401, start_ns=500 * MS)
    lines += steady(401, start_ns=12_500 * MS)
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 1
    assert r["stalls"] == [{"at_s": 10.0, "duration_s": 2.0}]
    assert r["duration_s"] == 22.0


def test_c7_duration_ends_at_last_kept_row_and_stall_to_artifact_counts(tmp_path):
    lines = steady(401) + [row(ARTIFACT, START_NS + 13 * S)]  # artifact 3 s after the end
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 1
    assert r["duration_s"] == 10.0
    assert r["stalls"] == [{"at_s": 10.0, "duration_s": 3.0}]


# ---- M5: real frames ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("fg", "real", "estimate"),
    [(1, 40.0, False), (2, 20.0, True), (3, 13.3, True), (4, 10.0, True)],
)
def test_m5_real_fps_divides_by_multiplier(tmp_path, fg, real, estimate):
    r = report(tmp_path, steady(300), fg=fg)
    assert r["fg_multiplier"] == fg
    assert r["avg_fps"] == 40.0
    assert r["real_avg_fps"] == real
    assert r["real_low_1pct_fps"] == real
    assert r["real_is_estimate"] is estimate


def test_c4_real_fps_come_from_unrounded_values(tmp_path):
    # avg = low = 24.94: unrounded / 2 = 12.47 -> 12.5; rounding first gives 24.9 / 2 -> 12.4
    r = report(tmp_path, grid([1000 / 24.94] * 300), fg=2)
    assert r["avg_fps"] == 24.9
    assert r["real_avg_fps"] == 12.5
    assert r["real_low_1pct_fps"] == 12.5


@pytest.mark.parametrize(
    "fg", [0, 5, -1, True, False, 2.0, "2", None], ids=lambda v: f"{type(v).__name__}_{v}"
)
def test_m5_invalid_fg_multiplier_raises(tmp_path, fg):
    log = measure.parse_log(str(write_log(tmp_path, steady(300))))
    with pytest.raises(measure.MeasureError):
        measure.analyze(log, fg_multiplier=fg)


# ---- M6: what limited it -----------------------------------------------------------


@pytest.mark.parametrize(
    ("loads", "limit", "share"),
    [
        ([90] * 6 + [10] * 4, "gpu", 0.6),  # exactly 90 counts; exactly 0.6 is gpu
        ([89.999] * 6 + [10] * 4, "not_gpu", 0.0),  # 89.999 is not busy; mean 58
        ([95] * 5 + [10] * 5, "mixed", 0.5),
        ([95] * 1 + [60] * 9, "not_gpu", 0.1),  # mean 63.5
        ([95] * 2 + [50] * 8, "mixed", 0.2),  # exactly 0.2 is not < 0.2
        ([75] * 10, "mixed", 0.0),  # mean exactly 75 is not < 75
        ([74.9] * 10, "not_gpu", 0.0),
        ([95] * 1 + [10] * 2, "mixed", 0.333),  # 1/3 rounds to 0.333
    ],
)
def test_m6_limit_and_gpu_busy_share(tmp_path, loads, limit, share):
    r = report(tmp_path, grid([25.0] * len(loads), gpu_load=loads))
    assert r["limit"] == limit
    assert r["gpu_busy_share"] == share


def test_m6_no_gpu_load_column_is_unknown(tmp_path):
    cols = [c for c in COLUMNS if c != "gpu_load"]
    lines = [row(25.0, START_NS + i * 25 * MS, columns=cols) for i in range(300)]
    r = report(tmp_path, lines, columns=cols)
    assert r["limit"] == "unknown"
    assert r["gpu_busy_share"] is None


# ---- M7 / C10: worst minute --------------------------------------------------------


def test_m7_worst_window_is_lowest_avg(tmp_path):
    # rel 0..35 s at 25 ms, 35..95 s at 50 ms, 95..125 s at 25 ms. Only the window
    # starting at 35 s holds just the slow stretch: 1200 frames, sum 25 + 1199*50.
    lines = [row(25.0, START_NS + k * 25 * MS) for k in range(1401)]
    lines += [row(50.0, START_NS + 35 * S + j * 50 * MS) for j in range(1, 1201)]
    lines += [row(25.0, START_NS + 95 * S + j * 25 * MS) for j in range(1, 1201)]
    r = report(tmp_path, lines)
    assert r["duration_s"] == 125.0
    assert r["worst_window"] == {"start_s": 35.0, "avg_fps": 20.0, "low_1pct_fps": 20.0}


def test_c10_tie_goes_to_earliest_on_unrounded_avg(tmp_path):
    # 125 s at 25 ms; one 26 ms frame at rel 100.05 s. Windows 45..65 contain it and
    # tie at 2400000/60001 = 39.9993 (rounds to 40.0 like every other window).
    frametimes = [25.0] * 5001
    frametimes[4002] = 26.0
    r = report(tmp_path, grid(frametimes, start_ns=0))
    assert r["worst_window"] == {"start_s": 45.0, "avg_fps": 40.0, "low_1pct_fps": 40.0}


def test_c10_constant_session_worst_window_is_the_first(tmp_path):
    r = report(tmp_path, steady(5001))
    assert r["worst_window"] == {"start_s": 0.0, "avg_fps": 40.0, "low_1pct_fps": 40.0}


def test_c10_windows_with_no_kept_rows_are_skipped(tmp_path):
    # 0..30 s at 25 ms, nothing until 100 s, then 100..170 s at 50 ms.
    # Windows 35 and 40 are empty; 45 is the earliest all-slow window.
    lines = [row(25.0, k * 25 * MS) for k in range(1201)]
    lines += [row(50.0, 100 * S + j * 50 * MS) for j in range(1401)]
    r = report(tmp_path, lines)
    assert r["worst_window"] == {"start_s": 45.0, "avg_fps": 20.0, "low_1pct_fps": 20.0}
    assert r["stalls"] == [{"at_s": 30.0, "duration_s": 70.0}]


def test_m7_short_session_is_one_window(tmp_path):
    r = report(tmp_path, steady(300))  # 7.475 s
    assert r["worst_window"] == {"start_s": 0.0, "avg_fps": 40.0, "low_1pct_fps": 40.0}
    assert "short_window" in r["warnings"]


def test_c10_exactly_60_s_gets_a_real_window(tmp_path):
    r = report(tmp_path, steady(2401))  # 2400 x 25 ms = 60.0 s
    assert r["duration_s"] == 60.0
    assert "short_window" not in r["warnings"]
    assert r["worst_window"] == {"start_s": 0.0, "avg_fps": 40.0, "low_1pct_fps": 40.0}


def test_c10_just_under_60_s_is_short_window(tmp_path):
    r = report(tmp_path, steady(2400))  # 59.975 s
    assert "short_window" in r["warnings"]
    assert r["worst_window"]["start_s"] == 0.0


# ---- C2: no kept frames ------------------------------------------------------------

NULL_WHEN_EMPTY = [
    "avg_fps",
    "median_fps",
    "low_1pct_fps",
    "low_0_1pct_fps",
    "real_avg_fps",
    "real_low_1pct_fps",
    "duration_s",
    "gpu_busy_share",
    "worst_window",
]


def assert_empty_report(r):
    assert r["frames"] == 0
    for key in NULL_WHEN_EMPTY:
        assert r[key] is None, key
    assert r["slower_than"] == {}
    assert r["limit"] == "unknown"
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == []
    assert r["hitches"] == 0


def test_c2_header_only_log(tmp_path):
    r = report(tmp_path, [])
    assert_empty_report(r)
    assert r["warnings"] == ["few_frames"]
    assert r["stalls"] == []
    assert r["artifact_rows"] == 0
    assert r["bad_rows"] == 0


def test_c2_all_rows_bad(tmp_path):
    r = report(tmp_path, [row("nan", START_NS), row(-1.0, START_NS + MS)])
    assert_empty_report(r)
    assert r["bad_rows"] == 2
    assert r["first_bad_line"] == 4
    assert r["warnings"] == ["few_frames", "bad_rows"]


def test_c2_only_an_artifact_row(tmp_path):
    r = report(tmp_path, [row(ARTIFACT, START_NS)])
    assert_empty_report(r)
    assert r["artifact_rows"] == 1
    assert r["warnings"] == ["few_frames", "artifact_rows"]


def test_c2_empty_log_with_frame_generation_does_not_divide(tmp_path):
    r = report(tmp_path, [], fg=4)
    assert_empty_report(r)
    assert r["fg_multiplier"] == 4
