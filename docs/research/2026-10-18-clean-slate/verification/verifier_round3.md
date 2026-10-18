## Verdict: PASS WITH FIXES

Revision 3 (commit e018ca0) fixes 10 of the 11 round-2 findings. N4 is only partly fixed. None of the new problems makes the doc claim that something works or is done, so nothing is at FAIL level. Two WARN items do need short text fixes: M1, where the 2.7 ms figure is contradicted by the doc's own measurement, and M2, where V1 is scored "Viable" against a test that §9 never runs. I edited nothing in the repo.

All line numbers refer to `/home/claude/deckforge/docs/design/CLEAN_SLATE_NATIVE.md` at e018ca0. Note paths are relative to `docs/research/2026-10-18-clean-slate/`.

## What I ran
- **CI checks:**
  - `python3 ci/tamper_check.py --base origin/main` → `tamper check: OK`
  - `ruff check . && ruff format --check .` → `All checks passed! / 8 files already formatted`
  - `pytest -q` → `33 passed`
  - The branch changes only files under `docs/`.
- **My arithmetic:** `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/v3/check3.py`
  ```
  35-37 fps claim (doc:351): 31.25-3 -> 35.4  31.25-4 -> 36.7
  W1:119 own items 2+0.6+0.5 = 3.1 ms -> 35.52 fps
  upper-bound row 0.5/2.5/5 -> [32.52, 34.78, 38.1]
  saving needed by low/avg ratio: {0.75: 7.48, 0.8: 5.89, 0.85: 4.3, 0.9: 2.72}
  measured 5th-pct low/avg ratio in the benchmark tool: 0.875 -> 1% ratio is <= this, so 0.90 is already ruled out
  bar at ratio <= 0.875: saving >= 3.51 ms (vs doc's ~2.7)
  note's 4 ms meets 0.85 bar? False ; 5 ms? True ; 5 ms at 0.80? False
  ```
  - 35–37 fps is correct (35.4–36.7).
  - The 4.3–7.5 ms range, the "5 ms only at 0.85" line and the 2.7 ms figure at a 0.90 ratio all recompute correctly. M1 explains why the 0.90 ratio itself is wrong.
- **Citations:** I printed every newly cited line:
  - correct: W1:26, W1:119, X:170, R4_cpu:119, R4_cpu:18/205 ("one anecdote"), R4_cpu:68/209, baselines:33, baselines:104, B_H:42, R4_gpu:132, E_F:31/37/112-113;
  - off by two lines: R4_gpu:48 (M5).

## Task 1: round-2 findings
| # | Status | Doc line |
|---|---|---|
| N1 V1 "Viable" misses its bar | RESOLVED as asked (option a) | 32, 197. New gap: M2 |
| N2 untraceable 5 ms, summed knobs | RESOLVED | 42, 241 ("upper bound", W1:119 cited). New wording problem: M3 |
| N3 benchmark tool vs gameplay | RESOLVED | 43, 371, 440-441. Its 2.7 ms figure is wrong: M1 |
| N4 scripts cited for numbers they don't check | PARTLY | lock30 citation dropped (370). README:60-63 rewritten. Still open: 357 says every row was recomputed, and 82 points to a re-check result "below" that doesn't exist (M4) |
| N5 SM2 14 vs 18 fps | RESOLVED | 163-164, 354 |
| N6 Capcom legal claim | RESOLVED | 453 |
| N7 save and config backups | RESOLVED | 298, 439 |
| N8 SM2 +15% vs +8% | RESOLVED | 354 |
| N9 citations | RESOLVED | 113 (W1:26), 246 (X:170) |
| N10 Wilds row | RESOLVED | 353 |
| N11 clarity | RESOLVED | 41 "faster"; 26 defines Conditional; 34 states V3's condition; 274 renames the undervolt to "Checked"; 33 adds the corruption risk |

## Task 2: new findings
**M1. WARN. The 2.7 ms benchmark-tool bar (doc:371) is contradicted by the doc's own benchmark measurement (doc:40).**
- The 2.7 ms figure assumes 1% lows run at 0.90× the average in the benchmark tool.
- But the doc's measured benchmark run is 32 fps average with 28 fps at the 5th-percentile low. That is a ratio of 0.875 at the 5th percentile, and the 1% low can only be lower.
- So the benchmark-tool bar is at least about 3.5 ms, not 2.7. (Output above: `saving >= 3.51 ms`.)
- The "provisional" conclusion still holds, but Fede will compare results against this number.
- **Fix (doc:371):** "There the bar would be about 2.7 ms at the note's 0.90 ratio. But the measured 28 fps at the 5th percentile against a 32 average (above) already puts the ratio at or below 0.875, so about 3.5 ms or more."

**M2. WARN. V1 is "Viable" by a test that no §9 step runs (doc:32, 197 vs doc:249, 440-446).**
- §1 and the §6 table now score V1 against E's bar (E_F:112-113): at equal Deck ms, at least 0.3 JOD and at least 58% preference over the nearest stock preset.
- But V1's experiments judge something else:
  - §6 "Judges" (249) and §9 step 4 (440) judge V1 by the Wukong lock;
  - step 5 (444) compares High against Medium-plus.
- No step runs the equal-ms comparison against a stock preset, so part 5 of the viability test is ✓ for a test that isn't scheduled.
- If Fede runs §9 as written, a central 2.5 ms saving lands between step 4's kill (<2 ms) and its pass (≥4.3 ms), and V1 gets no verdict.
- **Fix:** add after doc:442: "Between 2 and 4.3 ms saved, V1 survives as a profile idea but not as the Wukong lock. Judge it on its own bar (`round2/E_F_search_autotune.md:112-113`: at least 0.3 JOD and at least 58% preference over Medium at equal Deck ms) by adding a Medium vs candidate pair to the step 5 panel." Add one line to doc:249 pointing to it.

**M3. WARN (clarity, mild R1). "Best estimate" sits above the "upper bound" (doc:42, 241, 351, 368, 370).**
- The doc calls W1's 3–4 ms "the best estimate in the notes", then calls its own 0.5/2.5/5 ms an "upper bound". The upper bound's central (2.5) is below the "best estimate". To Fede that reads as a contradiction.
- W1's 3–4 ms is also a sum of overlapping knobs, which R4_gpu:236 forbids.
- Its own items add to 3.1 ms, not 4.
- Round 4 cut its mip-bias piece from about 0.6 ms to about 0.2 ms (R4_gpu:242).
- **Fix:**
  - doc:42: "The highest estimate in the notes is 3–4 ms (W1:119; its items add to 3.1 ms, and round 4 trimmed the mip-bias piece, R4_gpu:242). My own itemisation gives 0.5 / 2.5 / 5 ms. Both add overlapping knobs, so both probably run high."
  - At 241, 351 and 368: "upper-bound estimate" → "my estimate (likely high)".
  - At 370: "The note's best 4 ms" → "The note's top figure, 4 ms".

**M4. NIT (R2). Evidence pointers.**
- doc:357 says the round-2 verifier recomputed "every row". Revision 3's new figures (35–37 fps, 2.7 ms) are not in `arith2.py.txt`.
- doc:82 says "its re-check result is below", and README:61 points back to that table. No result exists, so each points at the other.
- §11 (doc:487) still mentions only the 13 findings from round 1.
- **Fix:**
  - doc:357: append "Revision 3's new figures (35–37 fps, 2.7 ms) are not in that script; re-verification pending."
  - doc:82: "Revision 3 addresses them; re-check pending (`verification/verifier_round3.md`)."
  - doc:487: "two verifiers found 13 and 11 errors in revisions 1 and 2".

**M5. NIT. Citation off by two lines.** doc:241 cites R4_gpu:48, which is the table's separator line. The FSR 0.4 ms value is at R4_gpu:50.

**Contradictions between §1, §6, §7 and §9:**
- None in the numbers. "Borderline to unlikely" matches at 43 and 351. The 1.1×/1.3× at 53 matches §7 (1.128/1.302).
- The only conflict between sections is M2.

**Rule conflicts:** none. Only `docs/` changed, and the tamper check is OK.

## Unconfirmed
- I did not re-fetch the external sources (the SDHQ review, the LPC slides, the Wukong benchmark thread).

## Plain-language summary for Fede
- **What changed:** text only, in the design doc and the research README, plus the round-2 verifier's report and scripts. No code. Nothing reads or writes your files today.
- **What could mislead you:**
  - The doc says lock tests in the benchmark tool are easier (about 2.7 ms). Your own measured numbers say the bar there is at least about 3.5 ms.
  - The settings-profile idea is called "viable" against a test that the three-week plan never actually runs. Add the one panel comparison, or read "viable" as "untested".
  - "Best estimate" (3–4 ms) and "upper bound" (2.5 ms central) are worded backwards. Both figures are probably optimistic.
- **What the plan would touch (manual steps):** game config files (copy each one first; that step is new), save folders (back them up before undervolting; also new), BIOS voltage offsets, and kernel settings (a reboot resets them).
- **What can't be undone:** a save corrupted by too low an undervolt if you skipped the backup, a SteamOS issue once filed, vendor letters once sent, and clips once shown to panel members.
- **How to undo the rest:** reboot for the kernel settings, reset the BIOS offsets in Setup, and restore your copied config files.

## Key facts to keep
The clean-slate design doc, revision 3 (branch `design/clean-slate-native`, commit e018ca0), was re-verified on 2026-10-18: PASS WITH FIXES.
- 10 of the 11 round-2 findings are resolved; N4 is partly resolved.
- The two WARNs:
  - the 2.7 ms benchmark-tool bar should be at least 3.5 ms, given the measured 28/32 ratio;
  - V1's "viable" bar (E_F:112-113) is not run by any §9 step.
