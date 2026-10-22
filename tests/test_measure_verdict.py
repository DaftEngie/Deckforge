"""deckforge.measure.analyze warnings + verdict: spec docs/specs/measure.md, M8, M9 + C1, C11.

CONTRACTS (written from the spec before any implementation exists)

analyze(log, *, fg_multiplier=1)["warnings"]                                       [M8]
  Postcondition: each that applies, in exactly this order:
    short_log (duration_s < 120), short_window (duration_s < 60),
    likely_loading_or_menus (gpu_load column present and kept mean < 50),
    few_frames (N < 300), bad_rows (bad_rows > 0), artifact_rows (>= 1 artifact).

analyze(...)["verdict"], ["reasons"]                                  [M9, C1, C11, C18]
  Postconditions, on UNROUNDED avg_fps, low_1pct_fps, real_low_1pct_fps:
    not_enough_data  if short_log, likely_loading_or_menus or few_frames applies, or N = 0
    gold             if avg >= 34.5 and low >= 33.0 and real_low >= 14.0
    good_enough      if avg >= 30.0 and low >= 28.0 and real_low >= 14.0
    fail             otherwise
  reasons: [] for gold and good_enough.
    not_enough_data: one line per cause, in this order (C18):
      "log is shorter than 120 s", "the graphics chip was mostly idle, likely loading
      or menus", "fewer than 300 frames"; for N = 0 exactly ["fewer than 300 frames"].
    fail: each failed good_enough test, in this order:
      "average {a} fps is below {t}", "1% low {b} fps is below {t}",
      "real-frame 1% low {c} fps is below {t}"
    with a/b/c = round(x, 1) formatted ".1f", unless that reaches the threshold, then
    math.floor(x * 10) / 10 (C18 replaces C11's always-floor); t formatted "g".
  Verdict fixtures use spread() (rows 500 ms apart) so they are >= 120 s and not
  forced to not_enough_data by short_log.

Item 19 (F3-F5), binding over the above where they differ:
  - gold also needs worst_window avg >= 34.5, good_enough needs it >= 30 (unrounded);
    the fail reason "worst minute averaged {w} fps, below {t}" goes last (C18 numbers).
  - bad_rows / (bad + non-bad data rows, blanks excluded) > MAX_BAD_SHARE (0.05) adds
    warning too_many_bad_rows right after bad_rows and forces not_enough_data with the
    reason "more than 5% of rows were unreadable", last among the C18 reasons.
  - no gpu_load column adds warning no_gpu_data at the very end; it never blocks a pass.
  Mixed-frame fixtures use front_loaded() so no window is slower than the whole log.

Item 21: short_log is judged on playing time = duration_s - (sum of stall durations
  between two kept rows, unrounded); duration_s and the worst minute are unchanged.
  front_loaded() therefore has no stalls (gaps under 1 s, playing time >= 120 s).
"""

import pytest
from test_measure_support import (
    COLUMNS,
    MS,
    START_NS,
    S,
    cumulative,
    front_loaded,
    grid,
    interleave,
    row,
    spread,
    steady,
    write_log,
)

from deckforge import measure

ARTIFACT = 22_000_000.0


def report(tmp_path, lines, fg=1, **kw):
    log = measure.parse_log(str(write_log(tmp_path, lines, **kw)))
    return measure.analyze(log, fg_multiplier=fg)


def mix(*groups):
    """mix((count, frametime), ...) -> front_loaded rows: 120 s, worst minute >= overall avg."""
    frametimes = [ft for count, ft in groups for _ in range(count)]
    return front_loaded(frametimes)


SHORT = "log is shorter than 120 s"
IDLE = "the graphics chip was mostly idle, likely loading or menus"
FEW = "fewer than 300 frames"
BAD_SHARE = "more than 5% of rows were unreadable"


# ---- M8: warnings ------------------------------------------------------------------


def test_m8_all_warnings_in_spec_order(tmp_path):
    lines = grid([25.0] * 10, gpu_load=10)  # rel 0 .. 225 ms
    lines.append(row(ARTIFACT, START_NS + 250 * MS, gpu_load=10))
    lines.append(row("nan", START_NS + 275 * MS, gpu_load=10))
    r = report(tmp_path, lines)
    assert r["warnings"] == [
        "short_log",
        "short_window",
        "likely_loading_or_menus",
        "few_frames",
        "bad_rows",
        "too_many_bad_rows",  # item 19 F5: 1 bad of 12 data rows
        "artifact_rows",
    ]


def test_m8_clean_long_log_has_no_warnings(tmp_path):
    r = report(tmp_path, steady(5001))  # 125 s, gpu_load 89
    assert r["warnings"] == []


def test_m8_short_log_boundary_120_s(tmp_path):
    assert "short_log" not in report(tmp_path / "a", steady(4801))["warnings"]  # 120.0 s
    assert "short_log" in report(tmp_path / "b", steady(4800))["warnings"]  # 119.975 s


def test_m8_likely_loading_boundary_mean_50(tmp_path):
    at_50 = report(tmp_path / "a", steady(300, gpu_load=50))
    below = report(tmp_path / "b", steady(300, gpu_load=49.9))
    assert "likely_loading_or_menus" not in at_50["warnings"]
    assert "likely_loading_or_menus" in below["warnings"]


def test_m8_likely_loading_needs_gpu_load_column(tmp_path):
    cols = [c for c in COLUMNS if c != "gpu_load"]
    lines = [row(25.0, START_NS + i * 25 * MS, columns=cols) for i in range(300)]
    r = report(tmp_path, lines, columns=cols)
    assert "likely_loading_or_menus" not in r["warnings"]


def test_m8_few_frames_boundary_300(tmp_path):
    assert "few_frames" in report(tmp_path / "a", steady(299))["warnings"]
    assert "few_frames" not in report(tmp_path / "b", steady(300))["warnings"]


def test_m8_bad_rows_warning(tmp_path):
    lines = steady(300) + [row("nan", START_NS + 300 * 25 * MS)]
    r = report(tmp_path, lines)
    assert r["bad_rows"] == 1
    assert "bad_rows" in r["warnings"]


def test_m8_artifact_rows_warning(tmp_path):
    lines = steady(300) + [row(ARTIFACT, START_NS + 300 * 25 * MS)]
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 1
    assert "artifact_rows" in r["warnings"]


# ---- M9: verdict boundaries (unrounded comparisons) --------------------------------


def test_m9_gold_at_exact_avg_threshold(tmp_path):
    # 345 frames, sum 175*28 + 170*30 = 10000 ms -> avg exactly 34.5; P99 = 30 -> 33.3
    r = report(tmp_path, mix((175, 28.0), (170, 30.0)))
    assert r["avg_fps"] == 34.5
    assert r["verdict"] == "gold"
    assert r["reasons"] == []


def test_m9_just_below_gold_avg_is_good_enough_although_it_rounds_to_34_5(tmp_path):
    # sum 174*28 + 171*30 = 10002 -> avg 34.4931, shown as 34.5
    r = report(tmp_path, mix((174, 28.0), (171, 30.0)))
    assert r["avg_fps"] == 34.5
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []


def test_m9_gold_at_exact_low_threshold(tmp_path):
    # P99 index for N=300 is 296; 1000 / (1000/33) == 33.0 exactly in floats
    r = report(tmp_path, mix((296, 20.0), (4, 1000 / 33)))
    assert r["low_1pct_fps"] == 33.0
    assert r["verdict"] == "gold"


def test_m9_just_below_gold_low_is_good_enough_although_it_rounds_to_33(tmp_path):
    r = report(tmp_path, mix((296, 20.0), (4, 30.31)))  # 1000/30.31 = 32.992
    assert r["low_1pct_fps"] == 33.0
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []


def test_m9_good_enough_at_exact_avg_threshold(tmp_path):
    # sum 200*32.5 + 100*35 = 10000 -> avg exactly 30.0; P99 = 35 -> 28.57
    r = report(tmp_path, mix((200, 32.5), (100, 35.0)))
    assert r["avg_fps"] == 30.0
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []


def test_m9_fail_just_below_good_avg_although_it_rounds_to_30(tmp_path):
    # sum 199*32.5 + 101*35 = 10002.5 -> avg 29.9925. front_loaded keeps the 35 ms
    # frames out of every window, so the worst minute is 1000/32.5 = 30.77 (passes).
    r = report(tmp_path, mix((199, 32.5), (101, 35.0)))
    assert r["avg_fps"] == 30.0
    assert r["worst_window"]["avg_fps"] == 30.8
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["average 29.9 fps is below 30"]


def test_m9_good_enough_at_exact_low_threshold(tmp_path):
    # 1000 / (1000/28) == 28.0 exactly; avg 39.8 is not enough for gold with low 28
    r = report(tmp_path, mix((296, 25.0), (4, 1000 / 28)))
    assert r["low_1pct_fps"] == 28.0
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []


def test_m9_fail_on_low(tmp_path):
    r = report(tmp_path, mix((296, 25.0), (4, 36.0)))  # 1000/36 = 27.78 -> round 27.8
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["1% low 27.8 fps is below 28"]


def test_m9_real_floor_exactly_14_passes(tmp_path):
    r = report(tmp_path, mix((296, 25.0), (4, 1000 / 28)), fg=2)  # 28.0 / 2 = 14.0
    assert r["real_low_1pct_fps"] == 14.0
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []


def test_m9_real_floor_fail(tmp_path):
    r = report(tmp_path, mix((296, 25.0), (4, 1000 / 28)), fg=3)  # 28 / 3 = 9.33
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["real-frame 1% low 9.3 fps is below 14"]


def test_m9_exactly_min_frames_gets_a_verdict(tmp_path):
    r = report(tmp_path, spread([25.0] * 300))
    assert r["frames"] == 300
    assert r["verdict"] == "gold"
    assert r["reasons"] == []


def test_m9_few_frames_is_not_enough_data_even_when_bad(tmp_path):
    r = report(tmp_path, spread([50.0] * 299))  # 149 s, so few_frames is the only cause
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [FEW]


# ---- C1: gold needs the real-frame floor --------------------------------------------


def test_c1_gold_on_screen_with_fg4_fails_real_floor(tmp_path):
    # on screen: avg 34.5, low 33.3 (gold); real low 33.33 / 4 = 8.33
    r = report(tmp_path, mix((175, 28.0), (170, 30.0)), fg=4)
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["real-frame 1% low 8.3 fps is below 14"]


def test_c1_gold_with_fg2_keeps_gold_when_real_floor_met(tmp_path):
    r = report(tmp_path, mix((175, 28.0), (170, 30.0)), fg=2)  # real low 16.7
    assert r["verdict"] == "gold"
    assert r["reasons"] == []


# ---- C11: reasons, order and floor rounding ---------------------------------------


def test_c11_reason_uses_floor_rounding_29_96_to_29_9(tmp_path):
    r = report(tmp_path, spread([1000 / 29.96] * 300))  # every minute is 29.96 too (F4)
    assert r["avg_fps"] == 30.0
    assert r["verdict"] == "fail"
    assert r["reasons"] == [
        "average 29.9 fps is below 30",
        "worst minute averaged 29.9 fps, below 30",
    ]


def test_c11_all_three_reasons_in_order(tmp_path):
    r = report(tmp_path, spread([50.0] * 300), fg=2)
    assert r["verdict"] == "fail"
    assert r["reasons"] == [
        "average 20.0 fps is below 30",
        "1% low 20.0 fps is below 28",
        "real-frame 1% low 10.0 fps is below 14",
        "worst minute averaged 20.0 fps, below 30",  # item 19 F4: always last
    ]


def test_c11_good_enough_has_no_reasons(tmp_path):
    r = report(tmp_path, spread([32.0] * 300))  # 31.25 fps
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []


# ---- C18: unrepresentative logs never pass; reasons match report rounding ----------


def test_c18_three_second_high_fps_log_is_not_enough_data(tmp_path):
    r = report(tmp_path, steady(376, 8.0))  # 375 x 8 ms = 3.0 s at 125 fps
    assert r["duration_s"] == 3.0
    assert r["frames"] == 376
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT]


def test_c18_sixty_second_low_gpu_log_gives_both_reasons_in_order(tmp_path):
    r = report(tmp_path, steady(1876, 32.0, gpu_load=30))  # 1875 x 32 ms = 60.0 s
    assert r["duration_s"] == 60.0
    assert r["avg_fps"] == 31.2  # 31.25 would be good_enough on a real session
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT, IDLE]


def test_c18_long_low_gpu_log_is_not_enough_data(tmp_path):
    r = report(tmp_path, spread([25.0] * 300, gpu_load=30))  # 149.5 s, 40 fps
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [IDLE]


def test_c18_all_three_causes_in_order(tmp_path):
    r = report(tmp_path, steady(10, gpu_load=10))
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT, IDLE, FEW]


def test_c18_short_failing_log_lists_causes_not_fail_reasons(tmp_path):
    r = report(tmp_path, steady(300, 50.0), fg=2)  # 14.95 s at 20 fps
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT]


def test_c18_no_frames_reason_is_only_fewer_than_300(tmp_path):
    r = report(tmp_path, [])
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [FEW]


def test_c18_short_log_boundary_120_s(tmp_path):
    at_120 = report(tmp_path / "a", steady(4801))  # 120.0 s
    below = report(tmp_path / "b", steady(4800))  # 119.975 s
    assert at_120["verdict"] == "gold"
    assert below["verdict"] == "not_enough_data"
    assert below["reasons"] == [SHORT]


def test_c18_gpu_mean_boundary_50(tmp_path):
    at_50 = report(tmp_path / "a", spread([25.0] * 300, gpu_load=50))
    below = report(tmp_path / "b", spread([25.0] * 300, gpu_load=49.9))
    assert at_50["verdict"] == "gold"
    assert below["verdict"] == "not_enough_data"
    assert below["reasons"] == [IDLE]


def test_c18_reason_number_rounds_like_report_24_75_to_24_8(tmp_path):
    # 3168 frames, 1888 x 40 ms + 1280 x 41 ms = 128000 ms (128 s of real time):
    # avg = 3168000 / 128000 = 24.75 exactly -> round 24.8 (floor would say 24.7).
    # P99 = 41 ms -> 24.39 -> 24.4.
    # Row order is 640 x 41, 1888 x 40, 640 x 41. Worst minute (F4) is [0, 60): the 640
    # rows at 41 ms (last at 26.199 s) plus 845 rows at 40 ms (26.239 .. 59.999 s):
    # 1485000 / (26240 + 33800) = 24.7335 -> 24.7.
    r = report(tmp_path, cumulative(interleave([40.0] * 1888 + [41.0] * 1280)))
    assert r["avg_fps"] == 24.8
    assert r["worst_window"] == {"start_s": 0.0, "avg_fps": 24.7, "low_1pct_fps": 24.4}
    assert r["verdict"] == "fail"
    assert r["reasons"] == [
        "average 24.8 fps is below 30",
        "1% low 24.4 fps is below 28",
        "worst minute averaged 24.7 fps, below 30",
    ]


def test_c18_reason_floors_29_96_because_rounding_reaches_30(tmp_path):
    r = report(tmp_path, spread([1000 / 29.96] * 300))
    assert r["avg_fps"] == 30.0
    assert r["reasons"] == [
        "average 29.9 fps is below 30",
        "worst minute averaged 29.9 fps, below 30",
    ]


def test_c18_low_reason_floors_27_96_because_rounding_reaches_28(tmp_path):
    r = report(tmp_path, mix((296, 25.0), (4, 1000 / 27.96)))
    assert r["low_1pct_fps"] == 28.0
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["1% low 27.9 fps is below 28"]


def test_c18_real_reason_rounds_13_86_to_13_9(tmp_path):
    r = report(tmp_path, spread([1000 / 41.58] * 300), fg=3)  # real 13.86
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["real-frame 1% low 13.9 fps is below 14"]


def test_c18_real_reason_floors_13_96_because_rounding_reaches_14(tmp_path):
    r = report(tmp_path, spread([1000 / 41.88] * 300), fg=3)  # real 13.96
    assert r["real_low_1pct_fps"] == 14.0
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["real-frame 1% low 13.9 fps is below 14"]


# ---- item 19 F4: the worst minute counts --------------------------------------------


def slow_minute(slow_ms, slow_rows):
    """About 10 min at 22.5 ms (44.4 fps) with one slow stretch from rel 45.0 s.

    Rows 0..2000 at 22.5 ms (row 2000 at 45.0 s, a multiple of WINDOW_STEP_S), then
    slow_rows at slow_ms, then 22000 rows at 22.5 ms (495 s more). Elapsed advances by
    each frame's own time, so the window [45, 105) holds row 2000 plus the slow rows
    whose elapsed is below 105 s.
    """
    return cumulative([22.5] * 2001 + [slow_ms] * slow_rows + [22.5] * 22000, gpu_load=95)


def test_f4_full_minute_at_20_fps_fails_with_worst_minute_reason_last(tmp_path):
    # N = 25201, sum = 2001*22.5 + 1200*50 + 22000*22.5 = 600022.5 ms -> avg 42.0.
    # Sorted, 1200 slow frames sit at indices 24001..25200; P99 index 24948 -> 50 ms.
    # Window [45, 105): 22.5 + 1199*50 = 59972.5 ms over 1200 rows -> 20.009 -> 20.0.
    r = report(tmp_path, slow_minute(50.0, 1200))
    assert r["duration_s"] == 600.0
    assert r["avg_fps"] == 42.0
    assert r["worst_window"] == {"start_s": 45.0, "avg_fps": 20.0, "low_1pct_fps": 20.0}
    assert r["verdict"] == "fail"
    assert r["reasons"] == [
        "1% low 20.0 fps is below 28",
        "worst minute averaged 20.0 fps, below 30",
    ]


def test_f4_worst_minute_alone_fails_good_enough(tmp_path):
    # Slow stretch 1740 x 34.5 ms (28.99 fps). Overall avg 25741000/600052.5 = 42.9 and
    # P99 = 34.5 ms -> 28.99 >= 28, so only the worst minute fails good_enough:
    # [45, 105) = 22.5 + 1739*34.5 = 60018 ms over 1740 rows -> 28.991 -> "29.0".
    r = report(tmp_path, slow_minute(34.5, 1740))
    assert r["avg_fps"] == 42.9
    assert r["low_1pct_fps"] == 29.0
    assert r["worst_window"]["start_s"] == 45.0
    assert r["worst_window"]["avg_fps"] == 29.0
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["worst minute averaged 29.0 fps, below 30"]


def test_f4_gold_missed_only_on_worst_minute_is_good_enough(tmp_path):
    # Slow stretch 2000 x 30 ms (33.3 fps). Overall avg 26001000/600022.5 = 43.3 and
    # P99 = 30 ms -> 33.33 >= 33: every gold test passes except the worst minute,
    # [45, 105) = 22.5 + 1999*30 = 59992.5 ms over 2000 rows -> 33.34 < 34.5 (>= 30).
    r = report(tmp_path, slow_minute(30.0, 2000))
    assert r["avg_fps"] == 43.3
    assert r["low_1pct_fps"] == 33.3
    assert r["worst_window"] == {"start_s": 45.0, "avg_fps": 33.3, "low_1pct_fps": 33.3}
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []


# ---- item 19 F5: too many unreadable rows ---------------------------------------------


def with_bad_rows(good, bad, blanks=0):
    """good spread rows at 25 ms (gold on their own), then bad rows, then blank lines."""
    lines = spread([25.0] * good)
    end = START_NS + good * 500 * MS
    lines += [row("nan", end + i * MS) for i in range(bad)]
    return lines + [""] * blanks


def test_f5_max_bad_share_constant():
    assert measure.MAX_BAD_SHARE == 0.05


def test_f5_exactly_5_percent_bad_is_not_too_many(tmp_path):
    r = report(tmp_path, with_bad_rows(380, 20))  # 20 / 400 = 0.05, not > 0.05
    assert r["bad_rows"] == 20
    assert r["warnings"] == ["bad_rows"]
    assert r["verdict"] == "gold"


def test_f5_just_over_5_percent_forces_not_enough_data(tmp_path):
    # 21 / 401 = 5.2%. The 100 blank lines are not data rows (21 / 501 would be 4.2%).
    r = report(tmp_path, with_bad_rows(380, 21, blanks=100))
    assert r["bad_rows"] == 21
    assert r["warnings"] == ["bad_rows", "too_many_bad_rows"]
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [BAD_SHARE]


def test_f5_reason_last_among_c18_reasons(tmp_path):
    lines = steady(10, gpu_load=10) + [row("nan", START_NS + 10 * 25 * MS, gpu_load=10)]
    r = report(tmp_path, lines)
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT, IDLE, FEW, BAD_SHARE]


def test_f5_artifacts_count_as_readable_rows(tmp_path):
    # 380 kept + 20 artifact rows are all non-bad: 21 bad / 421 = 4.99% -> not too many.
    lines = spread([25.0] * 380)
    end = START_NS + 380 * 500 * MS
    lines += [row(ARTIFACT, end + i * 25 * MS) for i in range(20)]
    lines += [row("nan", end + 600 * MS + i * MS) for i in range(21)]
    r = report(tmp_path, lines)
    assert r["artifact_rows"] == 20
    assert r["bad_rows"] == 21
    assert "too_many_bad_rows" not in r["warnings"]
    assert r["verdict"] == "gold"


# ---- item 19 F3: no GPU data is a warning, not a block -------------------------------

NO_GPU_COLUMNS = [c for c in COLUMNS if c != "gpu_load"]


def no_gpu_rows(n, step_ns=500 * MS):
    return [row(25.0, START_NS + i * step_ns, columns=NO_GPU_COLUMNS) for i in range(n)]


def test_f3_no_gpu_data_warning_does_not_block_a_pass(tmp_path):
    r = report(tmp_path, no_gpu_rows(300), columns=NO_GPU_COLUMNS)  # 149.5 s at 40 fps
    assert r["limit"] == "unknown"
    assert r["warnings"] == ["no_gpu_data"]
    assert r["verdict"] == "gold"
    assert r["reasons"] == []


def test_f3_no_gpu_data_is_last_in_warning_order(tmp_path):
    lines = no_gpu_rows(10, 25 * MS)
    lines.append(row(ARTIFACT, START_NS + 250 * MS, columns=NO_GPU_COLUMNS))
    lines.append(row("nan", START_NS + 275 * MS, columns=NO_GPU_COLUMNS))
    r = report(tmp_path, lines, columns=NO_GPU_COLUMNS)
    assert r["warnings"] == [
        "short_log",
        "short_window",
        "few_frames",
        "bad_rows",
        "too_many_bad_rows",
        "artifact_rows",
        "no_gpu_data",
    ]


def test_f3_not_gpu_limit_alone_does_not_block_a_pass(tmp_path):
    # GPU at 60%: limit not_gpu (0 busy rows, mean 60 < 75) but mean >= 50, not idle.
    r = report(tmp_path, spread([25.0] * 300, gpu_load=60))
    assert r["limit"] == "not_gpu"
    assert r["warnings"] == []
    assert r["verdict"] == "gold"


# ---- item 20: a damaged gpu_load must not change the verdict ------------------------


def menu_log():
    """9000 rows at 16.6 ms (8999 x 16.6 ms = 149.4 s), GPU 30% busy: menus."""
    return steady(9000, 16.6, gpu_load=30)


def test_c20_menu_log_is_not_enough_data(tmp_path):
    r = report(tmp_path, menu_log())
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [IDLE]


def test_c20_one_garbage_gpu_value_keeps_menu_log_not_enough_data(tmp_path):
    lines = menu_log()
    lines[4000] = row(16.6, START_NS + 4000 * 16_600_000, gpu_load=1000000)
    r = report(tmp_path, lines)
    assert r["bad_rows"] == 1
    assert r["frames"] == 8999
    assert r["warnings"] == ["likely_loading_or_menus", "bad_rows"]
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [IDLE]


def test_c20_out_of_range_gpu_counts_toward_bad_share(tmp_path):
    # 380 good rows + 21 rows at gpu_load 150: 21 / 401 > 5% (F5 still applies)
    lines = spread([25.0] * 380)
    end = START_NS + 380 * 500 * MS
    lines += [row(25.0, end + i * 25 * MS, gpu_load=150) for i in range(21)]
    r = report(tmp_path, lines)
    assert r["bad_rows"] == 21
    assert "too_many_bad_rows" in r["warnings"]
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [BAD_SHARE]


# ---- item 21: short_log is judged on playing time -----------------------------------


@pytest.mark.parametrize(
    ("extra_ns", "duration", "stall"),
    [(900 * S, 950.0, 900.0), (23 * 3600 * S, 82850.0, 82800.0)],
    ids=["plus_900_s", "plus_23_h"],
)
def test_c21_damaged_last_elapsed_keeps_50_s_log_short(tmp_path, extra_ns, duration, stall):
    # 2001 rows at 25 ms (0 .. 50 s, 40 fps, GPU busy); the last row's elapsed is pushed
    # forward. Playing time = duration - stall = 49.975 s < 120.
    lines = [row(25.0, i * 25 * MS, gpu_load=95) for i in range(2000)]
    lines.append(row(25.0, 2000 * 25 * MS + extra_ns, gpu_load=95))
    r = report(tmp_path, lines)
    assert r["frames"] == 2001
    assert r["duration_s"] == duration
    assert r["stalls"] == [{"at_s": 50.0, "duration_s": stall}]
    assert "short_log" in r["warnings"]
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT]


def two_blocks(second_rows, gap_s=30):
    """0 .. 60 s at 25 ms (2401 rows), a gap_s stall, then second_rows rows at 25 ms."""
    lines = [row(25.0, k * 25 * MS) for k in range(2401)]
    start = (60 + gap_s) * S
    return lines + [row(25.0, start + k * 25 * MS) for k in range(second_rows)]


def test_c21_playing_time_exactly_120_s_with_a_stall_is_not_short(tmp_path):
    r = report(tmp_path, two_blocks(2401))  # 150 s - 30 s stall = 120.0 s playing
    assert r["duration_s"] == 150.0
    assert r["stalls"] == [{"at_s": 60.0, "duration_s": 30.0}]
    assert "short_log" not in r["warnings"]
    assert r["verdict"] == "gold"


def test_c21_playing_time_just_under_120_s_with_a_stall_is_short(tmp_path):
    r = report(tmp_path, two_blocks(2400))  # 149.975 s - 30 s = 119.975 s playing
    assert r["stalls"] == [{"at_s": 60.0, "duration_s": 30.0}]
    assert "short_log" in r["warnings"]
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT]


def test_c21_long_healthy_log_with_10_minute_stall_judged_normally(tmp_path):
    # 0 .. 150 s, a 600 s suspend, 750 .. 900 s; all at 40 fps: 300 s playing.
    lines = [row(25.0, k * 25 * MS) for k in range(6001)]
    lines += [row(25.0, 750 * S + k * 25 * MS) for k in range(6001)]
    r = report(tmp_path, lines)
    assert r["duration_s"] == 900.0
    assert r["stalls"] == [{"at_s": 150.0, "duration_s": 600.0}]
    assert r["warnings"] == []
    assert r["verdict"] == "gold"


def test_c21_stall_to_an_artifact_is_not_subtracted(tmp_path):
    # 0 .. 130 s kept, then an artifact 30 s later as the LAST row. Still valid under
    # item 22: no kept row follows the artifact, so there is no gap between consecutive
    # kept rows to subtract; playing time = duration_s = 130 s (not 100 s).
    lines = [row(25.0, k * 25 * MS) for k in range(5201)]
    lines.append(row(ARTIFACT, 160 * S))
    r = report(tmp_path, lines)
    assert r["duration_s"] == 130.0
    assert r["stalls"] == [{"at_s": 130.0, "duration_s": 30.0}]
    assert "short_log" not in r["warnings"]
    assert r["verdict"] == "gold"


# ---- item 22: stalls between consecutive kept rows, lone spikes ---------------------


def test_c22_long_gap_ending_in_artifact_is_subtracted(tmp_path):
    # Verifier round 4: 2000 rows at 25 ms (0.025 .. 50.0 s), 10 min with no frames, one
    # uptime-glitch artifact at 650 s (22778400 > 2 x 600000 ms), 800 rows to 670.0 s.
    # Kept rows 50.0 s -> 650.025 s are consecutive kept rows: that 600.025 s gap is
    # subtracted, so playing time = 669.975 - 600.025 = 69.95 s < 120.
    lines = [row(25.0, (i + 1) * 25 * MS, gpu_load=95) for i in range(2000)]
    lines.append(row(22778400.0, 650 * S, gpu_load=95))
    lines += [row(25.0, 650 * S + (i + 1) * 25 * MS, gpu_load=95) for i in range(800)]
    r = report(tmp_path, lines)
    assert r["frames"] == 2800
    assert r["artifact_rows"] == 1
    assert r["duration_s"] == 670.0
    assert r["stalls"] == [{"at_s": 50.0, "duration_s": 600.0}]
    assert r["warnings"] == ["short_log", "artifact_rows"]
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT]


def test_c22_long_gap_with_bad_row_inside_is_subtracted(tmp_path):
    # Same shape, but the row inside the gap is a bad row (gpu_load nan) at 350 s.
    lines = [row(25.0, (i + 1) * 25 * MS, gpu_load=95) for i in range(2000)]
    lines.append(row(25.0, 350 * S, gpu_load="nan"))
    lines += [row(25.0, 650 * S + (i + 1) * 25 * MS, gpu_load=95) for i in range(800)]
    r = report(tmp_path, lines)
    assert r["bad_rows"] == 1
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == [SHORT]


def thirty_minutes_with_slow_stretch():
    """Verifier round 4: 900 s at 25 ms, 50 s at 50 ms (20 fps), 850 s at 25 ms.

    Rows: 36000 at 0.025 .. 900.0 s, 1000 at 900.05 .. 950.0 s, 34000 at 950.025 ..
    1800.0 s; elapsed = t0 + (i + 1) x frame time.
    """
    a = [row(25.0, (i + 1) * 25 * MS, gpu_load=95) for i in range(36000)]
    slow = [row(50.0, 900 * S + (i + 1) * 50 * MS, gpu_load=95) for i in range(1000)]
    b = [row(25.0, 950 * S + (i + 1) * 25 * MS, gpu_load=95) for i in range(34000)]
    return a + slow + b


def test_c22_thirty_minute_log_with_slow_stretch_fails(tmp_path):
    # 71000 frames, sum 1800000 ms -> avg 39.4; P99 index 70289 -> 50 ms -> 20.0.
    # Worst minute: [890, 950) etc. = 1400 rows / 60000 ms = 23.33, earliest 890.
    r = report(tmp_path, thirty_minutes_with_slow_stretch())
    assert r["bad_rows"] == 0
    assert r["worst_window"] == {"start_s": 890.0, "avg_fps": 23.3, "low_1pct_fps": 20.0}
    assert r["verdict"] == "fail"


def test_c22_one_spiked_row_before_slow_stretch_still_fails(tmp_path):
    # The last row of the first block (900.0 s) is pushed +55 s to 955.0 s. It is
    # greater than the next row (900.05 s), and 900.05 >= the previous non-bad row
    # (899.975 s): only that row is bad. 70999 frames: avg 39.4, P99 index 70289 ->
    # 50 ms -> 20.0; worst minute [890, 950): 1399 rows / 59975 ms = 23.33 -> 23.3.
    lines = thirty_minutes_with_slow_stretch()
    lines[35999] = row(25.0, 955 * S, gpu_load=95)
    r = report(tmp_path, lines)
    assert r["bad_rows"] == 1
    assert r["frames"] == 70999
    assert r["avg_fps"] == 39.4
    assert r["low_1pct_fps"] == 20.0
    assert r["worst_window"] == {"start_s": 890.0, "avg_fps": 23.3, "low_1pct_fps": 20.0}
    assert r["warnings"] == ["bad_rows"]
    assert r["verdict"] == "fail"
    assert r["reasons"] == [
        "1% low 20.0 fps is below 28",
        "worst minute averaged 23.3 fps, below 30",
    ]


# ---- item 24: a damaged first-row elapsed must not hide a slow opening --------------


def slow_opening(spike_first):
    """Verifier round 5: 1100 rows at 50 ms (0.05 .. 55.0 s), 48000 at 25 ms (to 1255 s)."""
    lines = [row(50.0, (i + 1) * 50 * MS, gpu_load=99) for i in range(1100)]
    lines += [row(25.0, 55 * S + (i + 1) * 25 * MS, gpu_load=99) for i in range(48000)]
    if spike_first:
        lines[0] = row(50.0, 56 * S, gpu_load=99)
    return lines


def test_c24_slow_opening_fails(tmp_path):
    # N 49100, sum 55000 + 1200000 = 1255000 ms -> avg 39.1; P99 index 48608 -> 50 ms.
    # Worst minute [0, 60) from 0.05 s: 1100 x 50 ms + 201 x 25 ms = 1301 / 60025 -> 21.7.
    r = report(tmp_path, slow_opening(spike_first=False))
    assert r["bad_rows"] == 0
    assert r["worst_window"] == {"start_s": 0.0, "avg_fps": 21.7, "low_1pct_fps": 20.0}
    assert r["verdict"] == "fail"


def test_c24_first_row_spike_does_not_turn_fail_into_pass(tmp_path):
    # First row's elapsed set to 56 s: 56 > 0.1 s (next row), so only it is bad.
    # N 49099, sum 1254950 ms -> avg 39.1; P99 index 48608 -> 50 ms -> 20.0.
    # Worst minute [0, 60) from 0.1 s: 1099 x 50 + 203 x 25 = 1302 / 60025 -> 21.7.
    r = report(tmp_path, slow_opening(spike_first=True))
    assert r["bad_rows"] == 1
    assert r["first_bad_line"] == 4
    assert r["frames"] == 49099
    assert r["avg_fps"] == 39.1
    assert r["low_1pct_fps"] == 20.0
    assert r["worst_window"] == {"start_s": 0.0, "avg_fps": 21.7, "low_1pct_fps": 20.0}
    assert r["warnings"] == ["bad_rows"]
    assert r["verdict"] == "fail"
    assert r["reasons"] == [
        "1% low 20.0 fps is below 28",
        "worst minute averaged 21.7 fps, below 30",
    ]


# ---- item 25: a shifted first timestamp must not hide the worst minute --------------


def verifier_round6(first_row_lowered_ns=0):
    """Cumulative timestamps from 10 s, gpu_load 89: 12000 rows at 25 ms (300 s), 1791 at
    33.5 ms (60 s), 12000 at 25 ms (300 s). Optionally only the first row's elapsed is
    lowered (it stays below the next row, so it is kept)."""
    lines = cumulative([25.0] * 12000 + [33.5] * 1791 + [25.0] * 12000, start_ns=10 * S)
    lines[0] = row(25.0, 10 * S - first_row_lowered_ns)
    return lines


@pytest.mark.parametrize("lowered_ms", [0, 900, 2500, 4000])
def test_c25_slow_minute_fails_wherever_the_first_row_sits(tmp_path, lowered_ms):
    # N 25791, sum 24000*25 + 1791*33.5 = 659998.5 ms -> avg 39.1. P99 index 25533 lands
    # on a 33.5 ms frame -> 29.85 (>= 28, < 33). Worst minute = the 1791 slow rows plus
    # one 25 ms neighbour: 1792000 / 60023.5 = 29.855 -> 29.9 < 30 -> fail. The window
    # does not depend on the first row: lowering it by 0.9 s shifted the 5 s grid off
    # the slow minute (30.0, a wrong good_enough).
    r = report(tmp_path, verifier_round6(lowered_ms * MS))
    assert r["bad_rows"] == 0
    assert r["frames"] == 25791
    assert r["avg_fps"] == 39.1
    assert r["low_1pct_fps"] == 29.9
    assert r["worst_window"]["avg_fps"] == 29.9
    assert r["worst_window"]["low_1pct_fps"] == 29.9
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["worst minute averaged 29.9 fps, below 30"]


def test_c25_verifier_clean_log_worst_minute_start(tmp_path):
    # Clean log: the tied windows start at the last fast row (299.975 s from the first
    # row) and the first slow row (300.0085 s); both round to 300.0.
    r = report(tmp_path, verifier_round6())
    assert r["worst_window"]["start_s"] == 300.0
