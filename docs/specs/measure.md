# Spec: `deckforge.measure` — read one gameplay log, report how it played

Status: approved for tests, 2026-10-21. The clarifier's answers are folded in below and are binding. Implements step 1 of the build order Fede approved. The
target comes from `docs/decisions/0002-experience-target.md`.

## Goal (one sentence, user-visible)

After Fede plays a game, one command reads the MangoHud frame-time log of that session and
reports in plain words:

- how smooth it was (average and 1% low, real and on screen);
- whether the graphics chip was the limit;
- the worst minute;
- whether the session met the target.

It changes nothing on disk.

## Delivery

- One PR, based on `main`.
- Standard library only (R8).
- Tests are new files under `tests/`, with fixtures built in `tmp_path`.

## The log format (taken from Fede's real Deck logs, MangoHud on SteamOS 3.8.28)

A frame log is a CSV file:

```
os,cpu,gpu,ram,kernel,driver,cpuscheduler
Steam Runtime 4,AMD Custom APU 0932,AMD Custom GPU 0932 (RADV VANGOGH),15159840,6.18.50-valve2-1-neptune-618-gc7289a96b14d,,powersave
fps,frametime,cpu_load,cpu_power,gpu_load,cpu_temp,gpu_temp,gpu_core_clock,gpu_mem_clock,gpu_vram_used,gpu_power,ram_used,swap_used,process_rss,cpu_mhz,elapsed
185.568,5.38885,80.4233,8.0826,89,75,66,958,800,0.926651,2,8.68896,0.375156,0,3403,10423837
```

- **Line 1:** system field names. **Line 2:** their values. **Line 3:** column names.
  **Line 4 onward:** one row per presented frame.
- **Units:**
  - `frametime` is in milliseconds.
  - `elapsed` is in nanoseconds since logging started.
  - `gpu_load` is a percentage.
- MangoHud also writes `<name>_summary.csv` next to each log. This module does not read it.

**Observed defect.** Some rows carry a `frametime` near 2.2e7 while `elapsed` advances
normally. The value looks like a wall-clock timestamp in milliseconds, not a real frame
time. In Fede's 2026-10-21 Wilds log, rows at 6.1 s and 52.5 s differ by exactly the
elapsed gap. These rows must not be read as stalls (M2).

## Interface

- `parse_log(path) -> MangoLog`
  - `MangoLog` is a frozen dataclass with fields `path: str`, `system: dict[str, str]`,
    `columns: list[str]`, `rows: list[dict[str, float]]`, `bad_rows: int` and
    `first_bad_line: int | None` (the file line number, 1-based).
- `analyze(log, *, fg_multiplier: int = 1) -> dict`: the report (M4–M9).
- `class MeasureError(Exception)`
- `main(argv: list[str] | None = None) -> int`
  - Positional `log` (optional).
  - `--logs-dir` (default `<home>/deckforge/logs`).
  - `--home` (default `os.path.expanduser("~")`).
  - `--fg-multiplier` (int, default 1).
  - `--json`.
- `__main__` guard: `raise SystemExit(main())`.
- Module constant `TARGET`, a dict:
  - `gold_avg=34.5`, `gold_low=33.0`;
  - `good_avg=30.0`, `good_low=28.0`, `real_low_floor=14.0`;
  - `min_frames=300`.
- Every rule below that names a threshold reads it from `TARGET`, or from the named
  constants `ARTIFACT_MS=10000`, `GAP_NS=1_000_000_000` and `WINDOW_S=60`.

## Acceptance criteria

**M1 Parse.**
- Line 3 must contain the required columns `fps`, `frametime` and `elapsed`. All other
  columns are optional. `system` maps line 1's names to line 2's values; on a length
  mismatch it is `{}`.
- A data row is dropped and counted in `bad_rows` (the first one sets `first_bad_line`)
  when:
  - its field count differs from line 3; or
  - any of its fields fails `float()`; or
  - any field is NaN or infinite.
- `MeasureError` is raised (one clear message) for:
  - fewer than 3 lines;
  - a missing required column;
  - a file larger than 64 MiB;
  - a file that isn't valid UTF-8;
  - a path whose name ends with `_summary.csv`. The message says to pass the frame log
    instead.
  - a path that is not a regular file. This is checked with `lstat`, so a link is refused.

**M2 Artifact rows.**
- A row is an **artifact** when its `frametime` is greater than `ARTIFACT_MS` and its
  `elapsed` is less than `GAP_NS` after the previous kept-or-artifact row. The first row
  counts as an artifact if its `frametime` is greater than `ARTIFACT_MS`.
- Artifacts are excluded from every metric and counted in `report["artifact_rows"]`.

**M3 Stalls.**
- A **stall** is an `elapsed` gap greater than `GAP_NS` between consecutive rows.
- It is reported in `report["stalls"]` as `{"at_s", "duration_s"}`, where `at_s` is the
  earlier row's elapsed time in seconds from the first row, rounded to 0.1.
- Separately, `report["hitches"]` counts kept frames whose `frametime` is over 100 ms.

**M4 Smoothness metrics, over kept frames.** Frame times are `F` in ms, and there are N
of them.
- **Percentiles:** `P(q)` is nearest-rank on the ascending sort, at index
  `ceil(q*N) - 1`.
- **Report fields:**
  - `frames`: N.
  - `duration_s`: (last elapsed − first elapsed) / 1e9.
  - `avg_fps`: 1000·N / ΣF.
  - `median_fps`: 1000 / P(0.5).
  - `low_1pct_fps`: 1000 / P(0.99).
  - `low_0_1pct_fps`: 1000 / P(0.999).
  - `slower_than`: `{"35": share, "30": share, "28": share}`, where each share is the
    fraction of F that is greater than 1000/x.
- **Rounding:** fps values to 1 decimal, shares to 3 decimals, in the JSON output.

**M5 Real frames.**
- `fg_multiplier` must be an int from 1 to 4. Otherwise `MeasureError`, which the CLI
  reports as exit 2.
- Calculations:
  - `real_avg_fps` = `avg_fps` / multiplier.
  - `real_low_1pct_fps` = `low_1pct_fps` / multiplier.
- `real_is_estimate` is true when the multiplier is greater than 1. The text report then
  says "estimated, assuming each real frame is shown N times".

**M6 What limited it** (`report["limit"]`).
- If there's no `gpu_load` column → `"unknown"`.
- Otherwise, let *g* be the share of kept rows with `gpu_load` ≥ 90:
  - `"gpu"` when *g* ≥ 0.6;
  - `"not_gpu"` when *g* < 0.2 and the mean `gpu_load` < 75;
  - `"mixed"` otherwise.
- `report["gpu_busy_share"]` is *g*, rounded to 3 decimals.
- **Plain text:**
  - gpu: "the graphics chip was the limit; graphics settings will raise fps";
  - not_gpu: "the graphics chip had room to spare; the limit was likely the processor, or a frame cap";
  - mixed: "a mix".

**M7 Worst minute.**
- Windows of `WINDOW_S` seconds by `elapsed`. They start at the first kept row and every
  5 s after, as long as the window ends at or before the last kept row's elapsed.
- For each window, compute the M4 avg and 1% low over kept rows in [start, start + 60 s).
- `report["worst_window"]` = `{"start_s", "avg_fps", "low_1pct_fps"}` for the lowest
  avg. On a tie, the earliest window wins.
- If `duration_s` < `WINDOW_S`, the window is the whole session and the warning
  `short_window` is added.

**M8 Is this log representative?** `report["warnings"]` lists, in this order, each that
applies:
- `short_log`: `duration_s` < 120;
- `short_window` (see M7);
- `likely_loading_or_menus`: there is a `gpu_load` column and the mean over kept rows is
  < 50;
- `few_frames`: N < `min_frames`;
- `bad_rows`: `bad_rows` > 0;
- `artifact_rows`: at least one artifact row.

**M9 Verdict against decision 0002** (`report["verdict"]`, `report["reasons"]`).
- `"not_enough_data"` if `few_frames` applies, or if N = 0.
- `"gold"` if `avg_fps` ≥ `gold_avg`, `low_1pct_fps` ≥ `gold_low` and `real_low_1pct_fps` ≥ `real_low_floor`.
- `"good_enough"` if `avg_fps` ≥ `good_avg`, `low_1pct_fps` ≥ `good_low` and
  `real_low_1pct_fps` ≥ `real_low_floor`.
- `"fail"` otherwise.
- `reasons` lists each failed `good_enough` test in this form:
  "average 24.8 fps is below 30". For gold and good_enough the list is empty.
- The comparisons use the unrounded values.

**M10 Output.**
- **Without `--json`:** a short plain-English report. It shows the file name, duration,
  every M4 fps value, real fps (M5), limit (M6), worst minute (M7), warnings (each
  explained in one line) and the verdict with its reasons.
- **With `--json`:** the report dict, `json.dumps(indent=2, sort_keys=True)`, with a
  trailing newline. The keys are those named in M2–M9 plus `file`, `fg_multiplier`,
  `bad_rows` and `system`.
- **Exit codes:**
  - 0 when a report is printed, whatever the verdict;
  - 2 on `MeasureError`, with exactly one line on stderr;
  - other exceptions propagate (R12).

**M11 Picking the log.**
- With no positional `log`, use the newest file by mtime in `--logs-dir`. Candidates are
  regular files only, checked with `lstat`; links are skipped. The name must end with
  `.csv` and not with `_summary.csv`.
- A tie on mtime goes to the name that sorts last.
- No candidates, or a missing folder → `MeasureError`.

**M12 Read-only.** Nothing is created, changed or deleted. Running the CLI on a fixture
leaves the fixture folder byte-for-byte unchanged, mtimes included.

## Out of scope

- **Writing settings, and the tuning loop.** `tune` comes later, through `deckforge.safety`.
- **Detecting frame generation automatically.** The caller passes `--fg-multiplier`. A
  later spec can read it from the game's settings.
- **Location labels.** The log does not say where in the game Fede was.
- **Desktop Mode detection.** The log header cannot tell Game Mode from Desktop Mode. The
  Deck guide tells Fede to measure in Game Mode only.

## Open assumption (UNSURE, to check on the Deck)

With in-game FSR3 frame generation on, MangoHud is assumed to count generated frames as
presented frames. That would make on-screen fps about 2× real.

The check is cheap. Play the same spot twice, with frame generation off and then on, and
compare `avg_fps`. Until that check is done, `--fg-multiplier 2` output is labelled
"estimated".

## Files and interfaces involved

- New: `src/deckforge/measure.py`, `tests/test_measure_*.py`.
- Imports: stdlib only, namely `argparse`, `csv`, `dataclasses`, `io`, `json`, `logging`,
  `math`, `os`, `stat`, `sys`.

## Safety

- **Reads:** one CSV log, or the listing of the logs folder.
- **Writes:** none.
- **Undo:** not needed.

## End-to-end check Fede will run on the Deck

1. Desktop Mode → Konsole.
2. `cd ~/deckforge-repo && git pull`.
3. Run:
   ```
   PYTHONPATH=src python3 -m deckforge.measure
   ```
   With frame generation on, add `--fg-multiplier 2`.
4. Read the report.
   - Expected for the 2026-10-21 Windward Plains log: about 24.8 fps average,
     limit `gpu`, verdict `fail`.

## Clarifier questions and answers (filled before tests are written)

Reviewed 2026-10-21 by the clarifier. Where an answer below differs from M1–M12 above,
the answer wins.

1. **Gold needs the real-frame floor too.** Otherwise `--fg-multiplier 4` could rate
   about 8.6 real fps as gold. This is consistent with decision 0002, where gold means a
   steady 17.5 real.
2. **No kept frames (N = 0).**
   - `frames` = 0.
   - Every fps field, `real_*`, `duration_s`, `gpu_busy_share` and `worst_window` are
     `null`.
   - `slower_than` is `{}`, `limit` = `"unknown"`.
   - `verdict` = `"not_enough_data"`, `reasons` = `[]`. Exit code 0.
   - No percentile or division is attempted.
   - Only `few_frames` and `bad_rows`/`artifact_rows` warnings can apply.
3. **Percentiles use integers only.** For q = k/1000 with k in {500, 990, 999}, the index
   is `(k*N + 999) // 1000 - 1`. For N = 1, every percentile is that frame.
4. **`analyze` returns the final, rounded dict.**
   - The verdict, reasons, worst-window choice and `limit` are all computed from
     unrounded values. `real_*` come from the unrounded on-screen values.
   - fps fields, `duration_s`, `stalls[].at_s`, `stalls[].duration_s` and
     `worst_window.start_s` round to 0.1. Shares round to 3 decimals.
   - `round()` is Python's built-in.
5. **The JSON and `analyze` key set is exactly:**
   `artifact_rows, avg_fps, bad_rows, duration_s, fg_multiplier, file, first_bad_line,
   frames, gpu_busy_share, hitches, limit, low_0_1pct_fps, low_1pct_fps, median_fps,
   real_avg_fps, real_is_estimate, real_low_1pct_fps, reasons, slower_than, stalls,
   system, verdict, warnings, worst_window`.
   - `file` is the base name.
   - `gpu_busy_share` is `null` without a `gpu_load` column.
6. **Artifact rule (replaces M2).**
   - A row is an artifact when `frametime` > `ARTIFACT_MS` **and** `frametime` > 2 × the
     gap in ms since the previous non-bad row.
   - The first non-bad row is an artifact if `frametime` > `ARTIFACT_MS`.
   - Cause, for the record: MangoHud computes `frametime = now - last_present_time`
     (MangoHud `src/overlay.cpp:313-317`). When `last_present_time` is 0, it writes the
     system uptime. A real frame can never be longer than the time that passed, which is
     why the gap comparison works.
7. **Order of rows.**
   - Bad rows are invisible to everything after M1.
   - Stalls are gaps between consecutive non-bad rows, kept or artifact.
   - `at_s`, `start_s` and `duration_s` are measured from the first **kept** row.
     `duration_s` = last kept elapsed − first kept elapsed.
8. **More bad rows.** A row is bad (M1) if:
   - `frametime` ≤ 0; or
   - `elapsed` < 0; or
   - `elapsed` is lower than the previous non-bad row's.
9. **File hygiene.**
   - Lines that are empty after stripping whitespace are skipped silently and are not
     bad rows.
   - CRLF is accepted, and a UTF-8 BOM on line 1 is removed.
   - Duplicate column names in line 3 → `MeasureError`.
10. **Windows, and new constants.**
    - Windows with no kept rows are skipped.
    - Windows start at kept-relative times 0, `WINDOW_STEP_S`, 2·`WINDOW_STEP_S` and so
      on, while start + `WINDOW_S` ≤ `duration_s`. Each window covers [start, start + `WINDOW_S`).
    - If no window qualifies because `duration_s` < `WINDOW_S`, the whole session is one
      window with `start_s` 0, and `short_window` applies.
    - Ties go to the earliest window, on unrounded avg.
    - New named constants:
      - `WINDOW_STEP_S=5`, `HITCH_MS=100`;
      - `GPU_BUSY_PCT=90`, `GPU_SHARE_HI=0.6`, `GPU_SHARE_LO=0.2`, `GPU_MEAN_LO=75`;
      - `LOADING_GPU_MEAN=50`, `SHORT_LOG_S=120`;
      - `SLOWER_THAN=(35, 30, 28)`, so the JSON keys are `"35"`, `"30"` and `"28"`.
11. **Reasons, in this order and with these exact strings:**
    - `"average {a} fps is below {t}"`;
    - `"1% low {b} fps is below {t}"`;
    - `"real-frame 1% low {c} fps is below {t}"`.
    - `{a}`, `{b}` and `{c}` are rounded **down** to 1 decimal (`math.floor(x*10)/10`,
      formatted `.1f`). `{t}` is the threshold formatted with `g`.
    - `not_enough_data`, `gold` and `good_enough` all give `reasons = []`.
12. **CLI.**
    - argparse usage errors keep argparse's own output and exit 2. They are exempt from
      the one-line rule.
    - `analyze` raises `MeasureError` for an `fg_multiplier` that is not an `int`, is a
      `bool`, or is outside 1–4.
    - A positional `log` wins over `--logs-dir`, with no error.
13. **Picking the newest log.**
    - Ties are compared on `st_mtime_ns`, then the name that sorts last wins.
    - Only lowercase `.csv` counts.
    - If the newest file fails to parse, that is the error; there is no fallback.
    - The logs folder itself may be a link (for example to the SD card) and is followed.
      File links inside it are skipped.
    - A missing or non-folder `--logs-dir` → `MeasureError`.
14. **Size and type are checked with `lstat` before opening.**
    - Exactly 64 MiB is allowed; larger is refused.
    - FIFOs, devices and sockets are "not a regular file".
15. **M12.**
    - The module adds no logging handlers.
    - Read access times may change. Tests check content and mtime only.
16. **Rows are frames.** MangoHud calls `try_log()` once per presented frame
    (`src/overlay.cpp`, in `update_hud_info_with_frametime`). Fede's log agrees:
    7,428 rows over 299.9 s at 24.8 fps.
17. **Decided after the tests were written, 2026-10-21.**
    - `real_is_estimate` is always a bool: `fg_multiplier > 1`. It is set even when
      N = 0.
    - `MangoLog.rows` holds every non-bad row, artifacts included. Classifying artifacts
      is `analyze`'s job.
    - A path that doesn't exist → `MeasureError` (exit 2).
    - `stalls[].at_s` is measured from the first **non-bad** row, so it is never
      negative. This replaces C7 for stalls only. Durations and windows still use the
      first kept row.
    - `first_bad_line` counts physical file lines, blank lines included.
18. **Found by running the code on Fede's real logs, 2026-10-21.**
    - **Unrepresentative logs never get a pass verdict.** The verdict is
      `"not_enough_data"` if `short_log`, `likely_loading_or_menus` or `few_frames`
      applies, or if N = 0.
      - Why: a 3.2 s title-screen log (`..._18-56-51.csv`) was rated `gold`, and a 60 s
        loading-and-menus log (`..._19-05-17.csv`) was rated `good_enough`. A wrong pass
        is the worst result (R1).
    - **`not_enough_data` explains itself.** `reasons` lists one line per cause, in this
      order and with these exact strings:
      - `"log is shorter than 120 s"`, where 120 is `SHORT_LOG_S` formatted with `g`;
      - `"the graphics chip was mostly idle, likely loading or menus"`;
      - `"fewer than 300 frames"`, where 300 is `min_frames`.
      - For N = 0 the list is `["fewer than 300 frames"]`. This replaces the
        "`reasons = []`" rule in C2 and C11 for `not_enough_data`.
    - **Numbers in reasons match the report.** `{a}`, `{b}` and `{c}` use the same
      rounding as the report (`round(x, 1)`, formatted `.1f`). Only if that rounded
      value is at or above the threshold does the reason use the round-down value
      instead. So 24.75 prints as "24.8", while 29.96 still prints as "29.9".
      - Why: the real log showed "average 24.8 fps" in the report but "24.7" in the
        reason.
19. **Decided after the verifier review, 2026-10-21 (F1–F5).** Default: a wrong pass is
    worse than a cautious "not enough data" (R1). Fede can loosen these later.
    - **F1, damaged rows.**
      - A data row that the `csv` module itself rejects is a bad row (M1). Examples are
        a field over the csv size limit, or a bare `\r` in a field.
      - If any of lines 1–3 is rejected, raise `MeasureError` with a message saying the
        header is unreadable.
      - Never a traceback. A log cut off by a crash can end in many zero bytes.
    - **F2, impossible frame times.**
      - A row with `frametime` below `MIN_FRAMETIME_MS = 0.1` is a bad row (C8). No game
        frame takes under 0.1 ms.
      - JSON output uses `allow_nan=False`.
    - **F4, the worst minute counts.**
      - `gold` also needs `worst_window.avg_fps` ≥ `gold_avg`.
      - `good_enough` also needs `worst_window.avg_fps` ≥ `good_avg`. Unrounded values
        are compared.
      - The new `fail` reason goes last, after the three in C11:
        `"worst minute averaged {w} fps, below {t}"`, using the C18 number rule.
      - When gold misses only because of its worst-minute test, the result is
        `good_enough` if that level's tests pass, as with the other gold tests.
    - **F5, too many unreadable rows.**
      - When `bad_rows` is more than `MAX_BAD_SHARE = 0.05` of all data rows (bad + non-
        bad, blank lines excluded), the warning `too_many_bad_rows` is added.
      - In the M8 order it goes right after `bad_rows`.
      - It forces `not_enough_data`, with the reason
        `"more than 5% of rows were unreadable"`, where 5 is `MAX_BAD_SHARE*100`
        formatted with `g`.
      - Its reason goes last among the C18 reasons.
    - **F3, kept as a known limit, warning only.** With no `gpu_load` column, the
      warning `no_gpu_data` is added at the end of the M8 list:
      "can't tell menus from gameplay without GPU load". It does not block a pass. A
      game capped at 35 fps with the chip half idle is a real pass, so `not_gpu` alone
      must not block one.
20. **Decided after the second verifier review, 2026-10-21.** A damaged value in any
    column the verdict reads must not change the verdict, crash the tool or freeze it.
    - **`gpu_load` out of range.** When the `gpu_load` column exists, a row whose
      `gpu_load` is below 0 or above 100 is a bad row (M1/C8). F5 still applies when
      this happens often.
    - **Absurd forward jump.** A row whose `elapsed` is more than
      `MAX_JUMP_NS = 86_400_000_000_000` (24 h) after the previous non-bad row is a bad
      row. The next rows are then compared with that same previous non-bad row.
    - **Speed.** Finding the worst minute must not step through empty stretches one at a
      time. Skipping straight to the first window that can contain a row gives the same
      result.
      - Performance bound: a log of 100,000 rows with one 23-hour gap is analysed in
        under 5 s.
21. **Decided after the third verifier review, 2026-10-21.**
    - **Short logs are judged on playing time.** `short_log` applies when
      `duration_s` − (sum of `stalls[].duration_s` between kept rows, unrounded) is
      below `SHORT_LOG_S`. Stalls are counted only when both rows are kept, and each
      stall is counted once. The reported `duration_s` and the worst-minute logic are
      unchanged.
      - Why: one damaged `elapsed` near the end of a 50 s log, or a 10-minute suspend
        followed by one frame, made the log look long enough to be rated gold.
    - **The text report never crashes on a file name.** It prints the file name with
      non-UTF-8 bytes shown as backslash escapes, so even a strict UTF-8 stdout
      can't fail.
22. **Decided after the fourth verifier review, 2026-10-21.**
    - **Playing time counts every gap between consecutive kept rows.** This replaces
      item 21's "both rows kept" wording.
      - The stall total subtracted for `short_log` is the sum of
        `elapsed[k+1] − elapsed[k]` over consecutive **kept** rows k, k+1, wherever that
        gap is over `GAP_NS`. Artifact and bad rows in between are ignored.
      - Why: a 10-minute pause that ended in a MangoHud glitch row (an artifact) was
        not subtracted, and 70 s of play was rated gold.
    - **A lone forward spike in `elapsed` drops only itself.** This amends C8.
      - Row *i* is bad if its `elapsed` is greater than the next data row's `elapsed`
        (the next row that passes the other M1 checks), **and** that next row's
        `elapsed` is ≥ the previous non-bad row's `elapsed`.
      - The next row is then judged against the previous non-bad row as usual.
      - Rows whose `elapsed` is lower than the previous non-bad row's are still bad
        (C8). That now only happens when a timeline really goes backwards, not after one
        spiked row.
      - Why: one damaged `elapsed` pushed 55 s forward made 1,199 following rows bad.
        That hid a 20 fps stretch, and the log was rated gold.
      - Known limit, accepted: two or more consecutive spiked rows still drop the rows
        after them, and F5 forces `not_enough_data` when that passes 5%.
23. **Clarification of item 22, 2026-10-21.** The "next data row" for the spike rule is
    the next row that passes the single-row checks: it parses, its values are finite,
    and its `frametime` and `gpu_load` are in range. The 24 h jump check is not used to
    choose it, which keeps parsing to one pass. This only matters in a contrived
    three-row pattern around a jump of more than 24 h. That pattern is accepted as is.
