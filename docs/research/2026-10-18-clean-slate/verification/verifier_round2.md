## Verdict: FAIL (close to passing)

Revision 2 fixed 9 of the 13 round-1 findings outright and 3 in part (one more is resolved as asked but leaves a gap, N7). All of section 7 recomputes correctly. One new problem has FAIL severity. **V1 is called "Viable", but it misses its own pass bar.** That is the same kind of headline mismatch that failed revision 1. Every fix below is a text edit to a few lines. Nothing needs rewriting. I edited nothing in the repo.

All doc lines refer to `/home/claude/deckforge/docs/design/CLEAN_SLATE_NATIVE.md`. Note paths are relative to `docs/research/2026-10-18-clean-slate/`.

## What I ran

- **CI checks:** `python3 ci/tamper_check.py --base origin/main` → `tamper check: OK`. `ruff check . && ruff format --check .` → `All checks passed! / 8 files already formatted`. `pytest -q` → `33 passed`. The branch changes only `docs/`.
- **My arithmetic:** `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/v2/arith2.py`. It recomputes section 7 with the doc's own method (doc:353-365):
  ```
  Wukong    18.52 | 19.09 / 20.89 / 24.11 | gain x1.031 / 1.128 / 1.302
  Stalker2  18.69 | 19.27 / 21.08 / 24.34
  Wilds     14.93 | 15.39 / 16.84 / 19.43
  Medium-plus 31.25 - 0.5/2.5/5 -> 32.52 / 34.78 / 38.1 fps
  avg needed for p99<=31.7 at .75/.80/.85: 23.77 / 25.36 / 26.95 ms; saving 7.48 / 5.89 / 4.30
  saving 5.0 ms meets only at 0.85; 2.5 ms meets at none
  schedule 18.58 days = 2.65 weeks
  ```
  Every figure in doc:41, 52, 345-349, 363-364 and the §9 title matches. The positive-control bar is also consistent (LPC's 70-73 → 47 ms is a 33-36% gain, against a ≥20% bar).
- **The saved round-1 scripts:** I ran `verification/arith.py.txt` and `lock30.py.txt` as saved, from the scratchpad. Output is quoted under N4.
- **New findings:** `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/v2/newfindings.py`. Output is quoted under each finding.
- **Citations:** I printed every line range revision 2 newly cites. Two are off by a few lines (N9).

## Task 1: round-1 findings

| # | Status | Evidence in revision 2 |
|---|---|---|
| 1 Wukong overclaim | PARTLY | Wording fixed: doc:42 "borderline… only if V1 lands near its best case"; Stalker 2 is now "unknown" (doc:45). The lock is now R4's definition (doc:111 = R4_gpu:196), and the step 4 bar is ≥4.3 ms (doc:432). Still open: the "best case" of 5 ms can't be traced to a note (N2). |
| 2 Three viable | PARTLY | doc:28 now says "one viable… short of the three". V2 and V3 are marked ✗ (doc:194-195). "Independent" was dropped (doc:22, 80). Still open: V1 also fails part 4 (N1). |
| 3 SM2 anti-cheat | RESOLVED | doc:32-33, 242, 269, 405 ("excluded from every step"), 407-409, 129 |
| 4 V1 budget, Half Rate | RESOLVED | doc:235 uses 3 / 8–12 / 20% (E_F:37). doc:357 no longer adds Half Rate on top. doc:52 now says 1.3× |
| 5 Label and reference | RESOLVED | doc:112-117. NIT: the idea is still named "perceived-High" (doc:32, 210) |
| 6 Legal | RESOLVED | doc:127, 426 (clock arms moved to Stalker 2), 444, 123. But doc:444 adds a legal reading no note supports (N6) |
| 7 Positive control | RESOLVED | doc:291, 440 (on the charger) |
| 8 Wilds lever | RESOLVED | doc:47, 320-323, 347 |
| 9 Plan length, R7 | RESOLVED | doc:403 "about three weeks" matches 18.6 days. doc:405 marks steps as manual or needs-bench-runner. NIT: steps 3 and 6 wait for a runner that doesn't exist yet, so the calendar time is longer than three weeks |
| 10 V2 undo | RESOLVED as asked | doc:293-299. New gap in N7 |
| 11 Tier scheme | RESOLVED | doc:89-93, 124, 257 |
| 12 SteamOS issue text | RESOLVED | doc:310-313 matches R4_cpu:8, 188, 197-198 |
| 13 Smaller items | PARTLY | Fixed: doc:284/286, 417-422, 437, 465, 346-347, 253, 139. Not fixed: SM2 horde gain is +15% at doc:348 but +8% at doc:283 (N8) |

**Section 1 clarity list:**
- "Viable" vs "works": RESOLVED (doc:26).
- Anti-cheat "likely": RESOLVED (doc:32-34).
- The two overclaims: RESOLVED in wording (doc:42, 45); see N2.
- "Best lever": RESOLVED (doc:47).
- The 1.1–1.2× bullet: RESOLVED (doc:52).
- "Medium-plus" explained: RESOLVED (doc:44).
- Undervolt in the BIOS, and its risk: PARTLY. doc:33 now says BIOS, but the corruption risk appears only at doc:294.
- Decisions list: RESOLVED (doc:56-58, 107-129).

## Task 2: new findings

**N1. FAIL. V1 is scored "Viable" against a bar it misses (doc:193 vs doc:245, 432, 41).**
- **What's wrong:**
  - Part 4 of the viability test (doc:187) is "an expected central gain at or above its own pass bar".
  - V1's own judge is the locked-30 definition (doc:245). Its pass bar is a saving of about 4.3 ms or more (doc:432). Its central estimate is 2.5 ms (doc:41).
  - V2 is marked ✗ for exactly this pattern (doc:194).
  - Scored the same way, V1 is not viable either, so the §1 headline "one viable idea" (doc:28) doesn't follow from the doc's own test.
- **Evidence:** `newfindings.py` → `V1 central saving 2.5 ms vs its own step-4 pass bar >= 4.30 ms -> meets part 4: False`.
- **Smallest fix, pick one:**
  - (a) doc:193: score V1 against E's falsification bar from E_F:112-113 (≥0.3 JOD, ≥58% preference; kill below 5% saved). The central +0.3 JOD / 8–12% (E_F:37) just meets it. Add: "The Wukong lock in §9 step 4 is a separate, harder target that the central estimate misses."
  - (b) Mark V1 "Conditional", and change doc:28 to "no viable idea yet, three conditional".

**N2. WARN. The only case that reaches the lock rests on a 5 ms figure that no note gives, built by a sum the doc itself forbids (doc:237, 41, 364).**
- **What's wrong:**
  - doc:219 says "Never add their savings together (R4_gpu:236)". doc:237 then adds them: 1 + 0.6 + 0.4 + 0.45 = 2.45 ms.
  - The pessimistic 0.5 ms and optimistic 5 ms appear in no note.
  - The parts are traceable: R4_gpu:132 (split reconstruction, 0.6), R4_gpu:48 (FSR mip bias, 0.4), and B_H:42 (Lumen 0.5 / 2 / 4 ms, halved by the author).
  - W1:119 is the note that itemised this exact question. It gives 3–4 ms in total.
  - W2_W4:73 says to count the larger of overlapping knobs, not the sum.
- **Evidence:** `newfindings.py` → `W1:119 best itemised total 4.0 ms >= 4.30? False; 'larger knob, not sum'… -> False`. On traceable figures, even the best case falls short of the 4.3 ms minimum.
- **Fix:**
  - doc:42: "borderline: even the best note estimate (3–4 ms, W1:119) is just short of the 4.3 ms minimum, so a lock needs the bench to beat the paper."
  - doc:237: label 0.5 / 2.5 / 5 as the author's estimate, an upper bound because the knobs overlap.

**N3. WARN. Step 4 doesn't say where the lock is measured, and in the benchmark tool the bar drops to about 2.7 ms (doc:432, 240, 363).**
- **What's wrong:**
  - The 4.3–7.5 ms range uses gameplay 1% lows (0.75–0.85×).
  - Steps 1, 4 and 5 use the frozen benchmark tool. baselines_stack.md:104 says the benchmark tool's ratio is about 0.90, which "is optimistic".
  - So a benchmark-tool "pass" would come at nearly the central estimate and would not show a lock in gameplay. Under R1, that is a wrong "done".
- **Evidence:** `newfindings.py` → `saving needed if step 4 is measured in the benchmark tool (ratio 0.90): 2.72 ms -> central 2.5 ms nearly meets it`.
- **Fix:** add to doc:432: "measured in pre-registered gameplay scenes. A pass in the benchmark tool alone is labelled provisional (its lows run about 0.90×, baselines_stack.md:104)."

**N4. WARN. The doc says the round-1 scripts checked its new numbers. They didn't (doc:351, 364; also doc:81 and README.md:60).**
- **What's wrong:** run as saved, `arith.py.txt` prints the revision 1 figures:
  - `Stalker 2 … cent 12% … 21.56 fps`, `opt … 26.94` (revision 2 says 21.1 / 24.3);
  - `Wilds menu+HR+sweep … 17.55` (revision 2 says 16.8);
  - `Medium-plus … minus 1/3/6 ms` (revision 2 uses 0.5 / 2.5 / 5).
  - Only the Wukong row (`opt 20% + sweep 4% -> 24.11`) matches.
  - `lock30.py.txt` tests 6 ms, not 5, and shows a pass at ratio 0.8 as well. That contradicts the doc's "only at 0.85" claim it is cited for.
  - doc:81 and README:60 also say "all addressed". Under R2, that is the author's statement, not evidence.
- **Fix:**
  - doc:351: "Wukong row checked by `verification/arith.py.txt`. The other rows are recomputed by the author, and re-verification is pending."
  - doc:364: drop the `lock30.py.txt` citation, or update the script to 0.5 / 2.5 / 5.
  - doc:81 and README:60: "addressed; re-verification pending".

**N5. WARN. Space Marine 2's horde figure prefers an estimate over a Deck measurement (doc:161, 348). This was already in revision 1 and round 1 missed it.**
- **What's wrong:** the doc says the worst hordes run "about 18 fps… scaled from the PS5" (that estimate is R4_cpu:208). The measured Deck figure is 14 fps (baselines_stack.md:33 and W3:19, from SDHQ). W3:4 actually treats 18 as the *optimistic, after-levers* result: "hordes go from 14 to about 18 fps optimistic".
- **Evidence:** `newfindings.py` → 14 × 1.15 = 16.1 fps vs 18 × 1.15 = 20.7 fps.
- **Fix:** doc:161 and 348: "measured about 14 fps in hordes (SDHQ, baselines:33); PS5 scaling suggests about 18 (est.)."

**N6. WARN. The Capcom note at doc:444 makes a legal claim no note supports.**
- **What's wrong:** the doc says "Frame-time logging is not program analysis". R4_cpu:119 says only that "Wilds analysis carries contract risk", and no note says logging is exempt. This also departs from the doc's own rule that legal readings are cautious (doc:478).
- **Fix:** "Whether frame-time logging counts as 'analyzing… data' is untested (R4_cpu:119). Fede's call; not legal advice."

**N7. WARN. Save files aren't backed up before the risky steps (doc:293-299, 429).**
- **What's wrong:**
  - The undervolt can silently corrupt saves (C_sched_power.md:112). Resetting the BIOS doesn't repair a save that has already been corrupted.
  - Step 4's manual config edits bypass `deckforge.safety`, and the checklist has no step to copy the original file first.
- **Fix:**
  - Add to doc:294: "Back up the game save folders before the first undervolt run. Corruption already written is not undone by resetting the BIOS."
  - Add to doc:429: "Copy each config file before editing it."

**N8. NIT. Space Marine 2 horde gain: +15% at doc:348 vs +8% at doc:283.** The +8% is the GPU pin alone (R4_cpu:68). The +15% is the whole stack (R4_cpu:209). Fix: say so in both places.

**N9. NIT. Two citations are off by a few lines.**
- doc:242 cites X:167, but "Mods Detected fires on user-config edits" is at X:170.
- doc:113 cites W1:16, but the "100% render scale" reference is at W1:26.

**N10. NIT. The Wilds row applies E's UE5-cvar range to a game that only has menu settings (doc:347).** E_F:31 says the cvar argument fits only 2 of the 5 games, and E_F:37's 20% is "UE5 at a cliff". Fix: show the pessimistic 15.4 fps only, and mark central and optimistic as not applicable.

**N11. NIT. Clarity for Fede.**
- doc:41 says "needs about 4.3–7.5 ms more per frame", which reads as "slower". It should say "each frame must get 4.3–7.5 ms faster".
- "Conditional" is never defined (doc:28, 33-34), and V3's condition isn't stated.
- "Guided" means two unrelated things: the CPU power mode (doc:261) and the undervolt (doc:270).
- The V2 row in §1 omits the corruption risk.

**Rule conflicts:** none confirmed.
- R7: the manual steps are Fede using his own Deck, not a dev session.
- R10: V1 and V2 writes go through `deckforge.safety`; for manual steps, see N7.
- Tiers: Space Marine 2 is now stricter than CLAUDE.md requires.
- R5 and R8: no tests, CI files or dependencies were touched.

## Task 3: verdict and exact fixes

FAIL, because of N1. With the fixes for N1 to N7 applied (about 12 lines of text), I would expect a PASS. N8 to N11 are optional.

## Unconfirmed

- The 54 ms baseline's TSR content is still open (doc:159 says so honestly).
- I did not re-fetch FSR 4 "early 2027" or the vkd3d-proton 2026-09-08 claim. Both were already in revision 1.

## Plain-language summary for Fede

- **What changed:** one design document plus the verifier's report and scripts. No code, and nothing touches your files today.
- **What could mislead you:**
  - §1 says one idea (the settings profiles) is "viable". By the doc's own scoring rule it is only conditional, unless the doc names a different bar.
  - The "Wukong might just lock at 30 in the best case" line rests on a 5 ms saving no note gives. The best figure in the notes falls just short.
  - Space Marine 2's horde number is an estimate (18 fps), while a real Deck measurement says 14.
- **What the plan would read or write:**
  - game config files (by hand in step 4);
  - kernel scheduler values (step 2; a reboot resets them);
  - /etc files (through the manifest);
  - BIOS voltage offsets (you set them).
- **What can't be undone:**
  - a save file corrupted by too low an undervolt (back up your saves first);
  - a public SteamOS issue once filed;
  - vendor letters once sent;
  - game clips once shown to panel members.
- **How to undo the rest:** reboot (kernel values); reset the BIOS offsets in Setup; restore config copies or use the safety manifest.

## Key facts to keep

The clean-slate design doc, revision 2 (branch `design/clean-slate-native`, commit 753c9a1), was re-verified FAIL on 2026-10-18. The arithmetic is correct and 9 of the 13 round-1 findings are resolved. New blocker: V1 is called "viable" although its central saving (2.5 ms) is below its own 4.3 ms lock bar. Also flagged:
- the optimistic 5 ms is untraceable and sums overlapping knobs;
- the step 4 lock must be measured in gameplay, not the benchmark tool;
- the verifier scripts are cited as checking numbers they don't compute;
- Space Marine 2's horde figure should be the measured 14 fps.
