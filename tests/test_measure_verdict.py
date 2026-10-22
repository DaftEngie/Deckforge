"""deckforge.measure.analyze warnings + verdict: spec docs/specs/measure.md, M8, M9 + C1, C11.

CONTRACTS (written from the spec before any implementation exists)

analyze(log, *, fg_multiplier=1)["warnings"]                                       [M8]
  Postcondition: each that applies, in exactly this order:
    short_log (duration_s < 120), short_window (duration_s < 60),
    likely_loading_or_menus (gpu_load column present and kept mean < 50),
    few_frames (N < 300), bad_rows (bad_rows > 0), artifact_rows (>= 1 artifact).

analyze(...)["verdict"], ["reasons"]                                       [M9, C1, C11]
  Postconditions, on UNROUNDED avg_fps, low_1pct_fps, real_low_1pct_fps:
    not_enough_data  if N < 300 (includes N = 0)
    gold             if avg >= 34.5 and low >= 33.0 and real_low >= 14.0
    good_enough      if avg >= 30.0 and low >= 28.0 and real_low >= 14.0
    fail             otherwise
  reasons: [] unless fail; for fail, each failed good_enough test, in this order:
    "average {a} fps is below {t}", "1% low {b} fps is below {t}",
    "real-frame 1% low {c} fps is below {t}"
  with a/b/c = math.floor(x * 10) / 10 formatted ".1f" and t formatted "g".
"""

from test_measure_support import COLUMNS, MS, START_NS, grid, interleave, row, steady, write_log

from deckforge import measure

ARTIFACT = 22_000_000.0


def report(tmp_path, lines, fg=1, **kw):
    log = measure.parse_log(str(write_log(tmp_path, lines, **kw)))
    return measure.analyze(log, fg_multiplier=fg)


def mix(*groups):
    """mix((count, frametime), ...) -> interleaved frame times on a 25 ms elapsed grid."""
    frametimes = [ft for count, ft in groups for _ in range(count)]
    return grid(interleave(frametimes))


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
    # sum 199*32.5 + 101*35 = 10002.5 -> avg 29.9925
    r = report(tmp_path, mix((199, 32.5), (101, 35.0)))
    assert r["avg_fps"] == 30.0
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["average 29.9 fps is below 30"]


def test_m9_good_enough_at_exact_low_threshold(tmp_path):
    # 1000 / (1000/28) == 28.0 exactly; avg 39.8 is not enough for gold with low 28
    r = report(tmp_path, mix((296, 25.0), (4, 1000 / 28)))
    assert r["low_1pct_fps"] == 28.0
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []


def test_m9_fail_on_low(tmp_path):
    r = report(tmp_path, mix((296, 25.0), (4, 36.0)))  # 1000/36 = 27.78
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["1% low 27.7 fps is below 28"]


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
    r = report(tmp_path, steady(300))
    assert r["frames"] == 300
    assert r["verdict"] == "gold"
    assert r["reasons"] == []


def test_m9_few_frames_is_not_enough_data_even_when_bad(tmp_path):
    r = report(tmp_path, steady(299, 50.0))
    assert r["verdict"] == "not_enough_data"
    assert r["reasons"] == []


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
    r = report(tmp_path, grid([1000 / 29.96] * 300))
    assert r["avg_fps"] == 30.0
    assert r["verdict"] == "fail"
    assert r["reasons"] == ["average 29.9 fps is below 30"]


def test_c11_all_three_reasons_in_order(tmp_path):
    r = report(tmp_path, steady(300, 50.0), fg=2)
    assert r["verdict"] == "fail"
    assert r["reasons"] == [
        "average 20.0 fps is below 30",
        "1% low 20.0 fps is below 28",
        "real-frame 1% low 10.0 fps is below 14",
    ]


def test_c11_good_enough_has_no_reasons(tmp_path):
    r = report(tmp_path, steady(300, 32.0))  # 31.25 fps
    assert r["verdict"] == "good_enough"
    assert r["reasons"] == []
