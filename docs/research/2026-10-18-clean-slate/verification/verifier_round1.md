## Verdict: FAIL

Three confirmed problems mean the doc can't go to Fede as written:
- **Wukong reachability is overclaimed.** The doc says Wukong "can probably hold a locked 30". By its own arithmetic it doesn't.
- **"Three viable ideas" doesn't meet the doc's own six-part definition.** V3 fails part 5 and V2 is weak on part 4.
- **The two-week plan runs Space Marine 2 experiments that the anti-cheat note says must wait for the publisher's written answer.**

Every fix is a local text edit. No rewrite is needed: the section 7 arithmetic is correct as computed, and the structure is sound. I edited nothing in the repo. My scripts are in `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/verify/` (`arith.py`, `lock30.py`).

## What I ran, per check

| Check | How it was exercised |
|---|---|
| 1 Traceability | Read the doc and all 24 notes plus the 4 briefs in full. Grepped specific claims. Fetched PR #8 with `gh api repos/DaftEngie/deckforge/pulls/8`; it matches the doc's quote ("30 fps with visuals on par with High… FSR + frame gen layered on top for 40+"). |
| 2 Arithmetic | `arith.py` and `lock30.py` (output below). |
| 3 Overclaiming | `lock30.py`, plus a check of each viable idea against the §6 definition. |
| 4 Contradictions | Line-by-line comparison, doc against notes. |
| 5 Rules | Compared against CLAUDE.md, the X note and the round 3 brief. `python3 ci/tamper_check.py --base origin/main` → `tamper check: OK`. The branch changes only `docs/design/CLEAN_SLATE_NATIVE.md` and `docs/research/2026-10-18-clean-slate/**`. |
| 6 Clarity | Read section 1 as the owner would. |

Key `arith.py` output:
```
cent 12% + sweep 1.5%              -> 46.81 ms = 21.36 fps; gain x1.15   (doc: 46.8 / 21.4 OK)
opt 25% + sweep 4% + HalfRate 1.4  -> 37.48 ms = 26.68 fps; gain x1.44   (doc: 37.5 / 26.7 OK)
opt 20% + sweep 4% (E_F's range, no Half Rate) -> 41.47 ms = 24.11 fps; gain x1.30
Medium-plus -1/-3/-6 ms -> 33.06 / 35.40 / 39.60 fps (doc 33/35/40 OK)
clean-lock average needed (ratio .75/.80/.85): [40.0, 37.5, 35.3]; saving needed 4.58 ms
Stalker 2 central -> 21.56 fps (doc "~21"); Wilds menu+HR -> 17.27, +sweep -> 17.55 (doc 17.5)
ppd 42.1 / 56.1 OK; 0.5 JOD = 63.2% OK; LPC delta 0.11 W OK
Section 9 sequential schedule = 18.5 days vs 14
```

`lock30.py` checks the Wukong claim against round 4's frame-time rule (uncapped p99 ≤ 31.7 ms):
```
V1 central -3 ms   avg 35.4 fps  p99 {0.75: 37.7, 0.8: 35.3, 0.85: 33.2}  meets: all False
V1 opt -6 ms       avg 39.6 fps  p99 {0.75: 33.7, 0.8: 31.6, 0.85: 29.7}  meets: False/True/True
central with XeSS (+1.5 ms, my est. from D_neural.md:9-10)  meets: all False
```

## Findings, most severe first

All doc lines are in `/home/claude/deckforge/docs/design/CLEAN_SLATE_NATIVE.md`. Note paths are relative to `docs/research/2026-10-18-clean-slate/`.

**1. FAIL. Wukong "probably" holds a locked 30 (doc:34, also 108 and 308).**
- **What's wrong:** The doc's own figures say a clean lock needs about a 37.5 fps average (doc:323). Its central Medium-plus estimate is 35.4 fps. Under round 4's definition the central case fails at every 1%-low ratio, and even the optimistic case only passes at ratios of 0.8 or better (`lock30.py`).
- **Evidence in the notes:**
  - W1_perceived_high.md:119 calls it "**borderline**".
  - W1:117: at a 30 cap the measured point already gives "about 1.5 hitches per second".
  - W1:120: the author's prior is that "FSR at 640×400 fails the 1-JOD worst-clip rule on fur and foliage; XeSS… costs more ms". The doc drops this.
  - The 1 / 3 / 6 ms savings at doc:201 trace only loosely to W1:119 ("3–4 ms", which includes F's 0.5 ms). Round 4 then cut mip bias from 0.6 to 0.2 ms (R4_gpu_perception.md:49).
  - The Stalker 2 claim "similar" (doc:37) has no Medium data at all. The only v2.0 Deck figure is "second-hand… **unverified**" (baselines_stack.md:35).
- **Fix:**
  - doc:34: "Wukong reaches a clean 30 lock only if V1 lands near its optimistic estimate. At the central estimate it averages about 35 fps, short of the ~37.5 needed (est.)."
  - doc:37: "Unknown: no v2.0 Deck measurement exists."
  - doc:108: "…becomes *possibly* reachable."
  - doc:308: "borderline."
  - Adopt round 4's test as the definition of a 30 lock (R4_gpu_perception.md:196: "≤1% missed presents at a 30 cap, or uncapped p99 ≤ 31.7 ms").
  - Raise step 4's pass bar (doc:383) from 3 ms to at least 4.6 ms, so that a "pass" actually delivers the claimed lock.

**2. FAIL. "Three viable ideas" (doc:21) is inconsistent with the doc's own six-part definition (doc:168–174).**
- **V3 fails part 5** ("two weeks or less, judged by a measurement"):
  - Its kill rule is "within 60 days" (doc:290), judged by whether "a maintainer acted", not by a measurement.
  - Its census item has "Expected value… about 0" (doc:282).
- **V2 is weak on part 4:** its central p99 gain of −5% (doc:245, C_sched_power.md:71) sits below its own pass bar of at least 8% (doc:254).
- **Part 2 is only partly met:**
  - The undervolt and SCHED_IDLE pieces of V2 were reviewed only in round 2 (C_sched_power.md:81–112). The 1100 MHz pin was proposed in round 3 (W3_cpu_wall.md:64) and reviewed only in round 4.
  - Round 4 agents saw the earlier notes (README.md:8), so "independent" (doc:170) and "no earlier reasoning" (doc:76) overstate.
- **Why it matters:** the loop's stop condition (doc:13, "at least three ideas are viable") is reported as met when it wasn't.
- **Fix:**
  - Relabel V3 as a "complementary channel (fails §6 part 5)".
  - Add one line at doc:245: "central estimate is below V2's own pass bar."
  - doc:21: say the loop ended with fewer than three viable ideas. Under R1, a labelled partial result is the right outcome.

**3. FAIL. Space Marine 2 experiments ignore the anti-cheat default (doc:25–26, 208, 390).**
- **What the doc does:**
  - Marks V1 and V2 as "Yes" for anti-cheat (doc:25–26).
  - Calls the SM2 config "an anti-cheat-safe config file" (doc:208).
  - Runs V2 arms on an SM2 hub and a horde set-piece in the first two weeks (doc:390).
- **Evidence:**
  - X_anticheat_legal_maint.md:142, X4: "no answer within 14 days means the item stays Tier I for that game. No account testing."
  - X:38: the scheduler changes are only "Safe-likely". X:115: E's risk on SM2 is "Low". X:167 names "Mods Detected fires on user-config edits" as an open risk.
  - R4_cpu_ecosystem.md:36: "EAC policy could not verify".
  - 00_brief_round3.md:96: "Never propose testing on a real account."
  - CLAUDE.md: anti-cheat games get Tier S only.
  - The doc's own line 420 says to ask the vendor in writing, but the plan never sends X4.
- **Fix:**
  - Add a step 0 to §9: send the X4 letters.
  - Gate all SM2 V1/V2 arms on a written answer. Until then, SM2 gets only the read-only sampler and Valve's own Quick Access Menu controls.
  - doc:25–26: "Likely (unconfirmed; vendor asked)". doc:208: "low risk (est.), pending Focus/Saber's answer".

**4. WARN. The V1 budget is inflated, and Half Rate Shading is counted twice (doc:200, 319–320, 324).**
- **Inflated range:** E_F_search_autotune.md:37 gives 3% / 8–12% / 20%. The doc uses 3% / 10–12% / ~25% without saying it changed them, and justifies ~12% by "including round 3's new knobs". R4_gpu_perception.md:236 says those knobs are "under E's umbrella; never sum them".
- **Double count:** The optimistic row adds Half Rate 1.4 ms on top of V1. The doc's own lines 182 and 191 put Half Rate inside V1's umbrella, and E_F:40 says "Do not add A… on top of E".
- **Wilds:** doc:324 adds 2.4 ms of Half Rate to a "~10%" menu gain (doc:202) that I can't trace to any note. A_G_vrs_reprojection.md:52 says Wilds' own VRS option bypasses the forced rate when it is on.
- **Effect:** Wukong optimistic drops from 26.7 to 24.1 fps, and the "about 1.4× at best" headline (doc:46) becomes about 1.3× (`arith.py`).
- **Fix:** Use E_F's range or label the change as the author's revision, drop Half Rate from the optimistic row, and recompute doc:46.

**5. WARN. The quality label claims more than the notes support, and the reference is left open (doc:110, 109).**
- "Medium-plus, perceived as High" is stronger than W1:103 ("perceived within X JOD of High") and R4:196 ("not reliably preferred over High").
- W1:20 treats indistinguishability as a separate, stronger claim needing about 155 two-choice (2AFC) trials.
- R4:183 points out the reference mismatch: High at native 100% in W1, High at 67% in the baselines. The doc leaves it unresolved; step 1 measures High at 67%.
- **Fix:** Use R4's label, and add a decision: which High is the reference, native 100% or 67%.

**6. WARN. The legal and contract lines are softened (doc:223, 378, 391).**
- **Personal use:** "Bench work is Fede's personal use" (doc:223) is offered as the mitigation. W5_ecosystem_upstream.md:174–183 says "the contract binds, not copyright", and purely private use "still breaches the licence on Wukong". Personal use lowers copyright risk, not contract risk.
- **Clock pins on Wukong:** step 3 (doc:378) pins the GPU clock on Wukong. R4_cpu_ecosystem.md:51 says "Wukong is a poor control: its EULA §8.3 risk covers the clock-changing arms. Swap it."
- **Wilds:** step 6's Wilds test (doc:391) carries no Capcom §8.1 note, although R4_cpu:119 flags "Wilds analysis carries contract risk".
- **Panel:** W1:132 asks whether captures may be shown to friends. That question is missing from the decisions, yet the panel needs 12 observers.
- **Fix:** Correct the personal-use sentence, move step 3's clock arms to Stalker 2 (or make them Fede's decision), add the Capcom note to step 6, and add a decision about showing captures.

**7. WARN. The positive control contradicts the charger caveat (doc:230 vs 256).**
- LPC measured on the charger, and the doc says testing at 15 W "is the gap DeckForge has to close" (doc:230).
- Yet Civ VI must reproduce a 20% or better worst-1% gain at 15 W (doc:256), and C_sched_power.md:150 says that if it fails, "the bench is broken, not the idea". The control assumes the very result being tested.
- **Fix:** Run the positive control on the charger, as LPC did. Treat the 15 W run as the test.

**8. WARN. The Wilds lever is overstated (doc:39, 310).**
- The doc calls Capcom's Switch 2 version Wilds' "best lever" and says it "closes the rest" of the gap.
- W5:78: it "does nothing for 'High-like'".
- R4_cpu:165: Capcom replies to individual packets less than 5% of the time (est.). R4_cpu:168: the ask is parked until Digital Foundry's analysis.
- The plains may be GPU-bound (W3:21), which kills the ask (W5:98).
- **Fix:** Call it a long-shot floor-raiser, gated on step 6's result.

**9. WARN. The two-week plan doesn't fit two weeks and conflicts with R7 (doc:362–364).**
- Run sequentially on one bench Deck, the steps take 18.5 days (`arith.py`).
- doc:364 says the Deck is "driven by Fede or, later, the bench runner". CLAUDE.md R7 says "The Deck is driven **only** by the bench runner (later phase)". Steps 3 and 6 need root tooling: a 10 Hz sampler and an interleaved ABAB test harness.
- **Fix:** Retitle the section, and mark the steps that need code as "after the bench runner exists", or turn them into manual checklists.

**10. WARN. V2 omits a user-safety risk and any undo path (doc:234, 258–261).**
- C_sched_power.md:112 says of the undervolt: "Risk: silent corruption". That could reach save files, and the doc doesn't mention it.
- V2 writes to sysfs, debugfs and /etc, but unlike V1 it says nothing about `deckforge.safety`, backups or undo (R10).
- **Fix:** Add a risk line and an undo line (reboot resets kernel values; BIOS offsets reset in Setup; /etc drop-ins are removed through the manifest).

**11. WARN. The tier scheme changes CLAUDE.md without a decision (doc:84–89).**
- The doc adopts S0/S1, which goes beyond CLAUDE.md's Tier S list (in-game settings files, launch options, TDP/fps cap, refresh rate, game-provided upscalers). It adds kernel scheduler writes, priority changes on the game's threads, and a BIOS undervolt.
- PR #8 already has a pending decision U8 on anti-cheat policy.
- **Fix:** Label it "proposed; CLAUDE.md is unchanged until Fede decides".

**12. WARN. The V3 SteamOS issue text is wrong, and this text gets filed publicly (doc:274, 276).**
- doc:274 says "Its `base_slice` effect is undone…", but Valve's script writes no `base_slice_ns`. Its five writes are three dead files plus `migration_cost_ns` and `nr_migrate` (C_sched_power.md:18, R4_cpu:181–183).
- doc:276 says "The corrected text is in R4 §8". R4 §8 (line 192) gives instructions for fixing the draft, not corrected text.
- **Fix:** Reword per R4:192: "dead writes plus a false error log; any base_slice write reverts on hotplug (upstream since 5.13)".

**13. NIT. Smaller inconsistencies and dropped labels.**
- SM2 central "~+5%" (doc:311) vs V2's own +3% for CPU-bound scenes (doc:246). R4_cpu:68 revised the pin to 0/+3/+8%.
- The GPU-bound row "≈0" (doc:247) hides C_sched_power.md:70's pessimistic −1.5%, which fails V2's own −1% guard.
- Step 2 is titled "read-only" (doc:372) but includes writes (doc:376).
- "sit the panel" (doc:398) conflicts with W1:30, which excludes the owner from the confirmatory data.
- doc:411 drops W5:195's "(est.)".
- Stalker 2 central is 21.6 fps, shown as "~21". The Wilds 17.5 needs the driver sweep, which the label "(menu + Half Rate)" omits.
- doc:35's caveat "the game has been patched since" misses the point: the run was in the frozen benchmark tool (E_F:83), so the relevant drift is SteamOS and Proton.
- doc:124 cites A_G, where the toggle-to-file link is "[inferred]" (A_G:11). Cite X:14, which has the SDHQ source.

## Section 1 clarity for Fede

These points mislead or would confuse a non-engineer:
- "Viable" reads as "works". Nothing has been tried, and viable here only means "worth a 2-week test".
- "Works with anti-cheat? Yes" should read "likely".
- "Probably hold a locked 30" and "Stalker 2 is similar" are both overclaims (finding 1).
- "Best lever" for Wilds overstates (finding 8).
- The 1.1–1.2× bullet lists the compositor and upstream fixes, which §7 never computes. The compositor idea (V4) actually costs native fps.
- "Medium-plus" is never explained.
- V2's "guided undervolt" doesn't say he'll be changing BIOS settings, or the risk.
- The decisions list leaves out the 45-vs-30 target, the tier change, and showing captures to friends.

## Unconfirmed

- **The 54 ms baseline.** I couldn't reproduce how the round 2 note derived it, so I can't tell whether it already includes round 3's corrected TSR cost (about 2× the round 2 assumption, W2_W4_gpu_fixed_cost.md:27).
- **The four author-checked facts.** I did not re-fetch them, but none contradicts the notes: LPC +0.11 W matches C:15; 4 Dec 2026 matches R4_cpu:155; EULA §8.3 matches X:67; 32/28 fps matches baselines:29.
- **Evidence retention.** 12 notes cite "source copies" in the session scratchpad. They exist now but won't survive a container restart.

## Plain-language summary for Fede

- **What changed:** one design document plus its research notes. No code, nothing installed.
- **What could break:** your decisions, if you trust the summary. It says Wukong "probably" locks at 30 fps; by its own math that's borderline at best. It says three ideas are viable; one fails its own definition and one is weak.
- **What the doc reads or writes now:** nothing on your files.
- **What its plan would touch:**
  - game config files (backed up through `deckforge.safety`);
  - kernel and power settings (reset on reboot);
  - /etc drop-ins (stay until removed);
  - BIOS undervolt (resettable in Setup; can silently corrupt data if set too low);
  - Space Marine 2 runs on your real account.
- **What can't be undone:**
  - an anti-cheat action on your Space Marine 2 account;
  - a public issue once filed;
  - clips once shown to panel members.
- **How to undo:** reboot for kernel values; reset BIOS offsets; restore configs from the safety manifest. For the account and the public issue, there is no undo. That's why the plan should wait for the publisher's written answer before running Space Marine 2 experiments.

## Key facts to keep

The clean-slate design doc (branch `design/clean-slate-native`) was verified FAIL on 2026-10-18. Main issues: Wukong 30-lock overclaim (central 35.4 fps vs 37.5 needed), V3 fails the "≤2 weeks" part of the viability definition, and Space Marine 2 experiments must be gated on the X4 vendor letters.
