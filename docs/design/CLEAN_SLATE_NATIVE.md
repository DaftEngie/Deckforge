# Clean-slate search: playing demanding games natively on the Steam Deck

- **Status:** research result, not a build plan.
- **Measured on a Deck by this project:** nothing.
- **Date:** 2026-10-18 (revision 4, after three independent verifier rounds; see `verification/`).
- **Evidence:** the raw notes are in `docs/research/2026-10-18-clean-slate/`, indexed in its `README.md`. References like `round2/C_sched_power.md:15` point into that folder.

---

## 1. The answer in plain words

**The request.** Fede asked for a fresh start:
- the goal: find a way to play demanding (PS5-era) games natively on the Deck;
- a team of sub-agents with different viewpoints;
- a loop until at least three ideas are viable;
- no hiding behind "the hardware is too weak".

**What was done.** Twenty agents worked in four rounds:
1. Seven specialists invented about 40 ideas.
2. Seven sceptics tried to break each idea, then tried to rescue it.
3. Four new specialists attacked the specific walls round 2 had exposed.
4. Two new sceptics, who had not taken part in earlier rounds, reviewed the round-3 ideas.

A separate verifier then checked this document against all the notes.

**Results.** "Viable" here means worth a two-week bench test. It does not mean "works": nothing has been tried yet. "Conditional" means worth trying, but the idea fails one part of its own test (named in the table).

By the six-part test in section 6, the loop ended with **one viable idea, two conditional ones and one complementary track**. That is **short of the three that were asked for.** Section 6 says why the loop stopped there.

| # | Idea | What it does | Status | Anti-cheat games? |
|---|---|---|---|---|
| V1 | **Deck "perceived-High" profiles** | Per-game settings and config-file profiles, found by measuring on a Deck and judged by a blind panel on the Deck's own screen | **Viable** as an idea: its central estimate meets its own test. It is **not** expected to deliver the harder Wukong 30-lock target. | Likely, since it touches in-game settings files only. Unconfirmed: vendor not yet asked. |
| V2 | **Stutter kit** | CPU power mode, scheduler fix, and a BIOS undervolt you set yourself, all from outside the game. If the undervolt is set too low, it can silently corrupt saves. | **Conditional**: worth one test, but its central gain is below its own pass bar | Not until the vendor answers in writing and you decide on the tier change (§3) |
| V3 | **Upstream and publisher evidence channel** | Turns bench measurements into fixes that Valve, Mesa, Proton and publishers ship | **Conditional**: worth doing, but success depends on maintainers acting, which no 2-week measurement can judge | Yes, since nothing runs on the Deck |
| V4 | Smoothness track | Camera re-aiming between frames, plus frame generation on top of a native 30 | Complementary: it never counts toward native fps | Re-aiming only if built into gamescope; frame generation (lsfg-vk) no |

**The honest ceiling.** No target game reaches a locked 30 fps natively at the High preset, and none reaches 45 fps at a High-like look. That holds even at the optimistic estimate.

Per game:
- **Black Myth: Wukong** is the closest. In August 2024 a user measured it at 32 fps average and 28 fps at the 5th-percentile low, using Medium settings with FSR at a 50% render scale on an OLED Deck, in the game's frozen benchmark tool.
  - For a clean 30 lock, each frame must get about 4.3–7.5 ms faster (est.).
  - The highest estimate in the notes for V1's saving at this look is 3–4 ms (`round3/W1_perceived_high.md:119`). Its items add to 3.1 ms, and round 4 trimmed its mip-bias piece (`round4/R4_gpu_perception.md:242`). My own itemisation gives 0.5 / 2.5 / 5 ms. Both add up overlapping knobs, so both probably run high.
  - So on paper the lock is **borderline to unlikely**. It needs the bench to beat the paper, and the lock must be shown in gameplay, not only in the benchmark tool.
  - Whether that "Medium-plus" look counts as High-like is for a blind panel to say. Nobody has tested it.
  - "Medium-plus" means the Medium preset with targeted upgrades and better reconstruction, tuned to look as close to High as possible.
- **Stalker 2:** unknown. No Deck measurement of the current version (v2.0) exists.
- **Space Marine 2:** the CPU limits it in hordes. If that CPU work is game simulation rather than render-thread work, it can probably run near-High graphics at today's frame rate. Only the publisher can lift the horde floor.
- **Monster Hunter Wilds:** only its own menu settings are usable, because every mod route bypasses its anti-tamper. A long-shot ask to Capcom could raise the plains floor at a below-High look. It is gated on a test that shows the plains are CPU-bound.
- **Alan Wake 2** stays about 11 fps at a High-like look (est.).

**Why "don't use hardware as an excuse" still ends here.**
- The PS5 has about 6.3× the Deck's GPU compute.
- Everything this study found that can be changed from outside a game's code yields about 1.1× in the central case and about 1.3× at best (est., §7). That covers settings, driver flags, scheduler and power.
- The rest of the gap sits in the game's own content and code, which only the publisher can change. That is what V3 is for.
- Every wall got rescue attempts. They are recorded in each note.

**Decisions only Fede can make** are in §3. The two that matter most:
- Does "a blind panel can't reliably prefer High over it" count as High-like?
- Is the upscaler allowed inside the native 30?

---

## 2. How the search ran

**The screenshot prompt.** Before the work started, Fede received its four answers, in the conversation:
1. what a top professional would do that wasn't asked;
2. the rawest material to start from;
3. the methods and tools;
4. what external evidence would show the result is right.

He also received the rewritten prompt. It became the shared brief, `00_brief_round1.md`, which asked for:
- raw evidence to start from: GPU captures, driver and kernel source, perception research;
- an "(est.)" label on every estimate;
- for every idea, a falsification experiment of two weeks or less, judged by a measurement rather than an opinion.

| Round | Agents | Viewpoints | Output |
|---|---|---|---|
| 1 | 7 | Console-port graphics, neural rendering, perception and display science, kernel/driver/compiler, power and thermal, offline precomputation, adjacent fields | About 40 ideas, clustered A–I (`00_round2_clusters.md`) |
| 2 | 7 | One sceptic per cluster; an anti-cheat, legal and maintenance reviewer; a baseline and stacking analyst | Verdicts, corrected budgets, measured baselines |
| 3 | 4 | Vision science and QA panels; UE5/RE Engine/Northlight engine programming; CPU profiling; ecosystem and upstream | Ideas aimed at five walls |
| 4 | 2 | New sceptics, given the notes but not the author's conversation | Verdicts on the round-3 ideas |
| check | 2 | Verifiers with fresh context | Revision 1: FAIL, 13 findings (`verification/verifier_round1.md`). Revision 2: FAIL, 11 findings (`verification/verifier_round2.md`). Revision 3: PASS WITH FIXES, 5 findings (`verification/verifier_round3.md`). Revision 4 applies them, and has not been re-checked. |

**Rules every agent followed:**
- no DRM, anti-tamper or anti-cheat circumvention;
- no redistribution of game code or assets;
- no live streaming of frames (offline precompute allowed);
- frame generation and reprojection never count toward native fps.

**A tier refinement, proposed and not adopted.** Round 2 proposed splitting Tier S (`round2/X_anticheat_legal_maint.md:9-13`):
- **S0:** outside the game process.
- **S1:** stock Valve binaries changed only through documented environment variables or config files.

**CLAUDE.md is unchanged until Fede decides (§3, decision 6).** Under the current CLAUDE.md, Tier S means in-game settings files, launch options, TDP/fps cap, refresh rate and game-provided upscalers. Kernel scheduler writes, priority changes on game threads and BIOS undervolts are not on that list.

---

## 3. Decisions only Fede can make

The repository and the conversation currently hold different targets:

| Source | Frame-rate target | Quality reference |
|---|---|---|
| `docs/QUALITY_TARGET.md` (2026-10-08) | median ≤22.2 ms (45 fps) | max settings at native 1280×800 |
| Fede's universal-feasibility request (PR #8) | 30 fps **without FSR or frame generation**; FSR and frame generation may lift it to 40+ | "on par with High settings" |
| This study's brief | ≥30 fps with good 1% lows; upscalers allowed because they run on the Deck; frame generation tracked separately | the High preset as perceived on the Deck's screen |

1. **Is an upscaler allowed inside the native 30?**
   - Every estimate here assumes yes.
   - If not, as in the PR #8 wording, every game falls further short. Nobody has even measured Wukong at Low without an upscaler.
2. **Which frame target: a locked-30 floor or a 45 fps median?**
   - This study uses "locked 30" as defined in `round4/R4_gpu_perception.md:196`: at most 1% missed presents at a 30 cap, or an uncapped p99 of 31.7 ms or less.
3. **Which High is the reference?** The options are the High preset at native 100% render scale, High at 67%, or max settings (QUALITY_TARGET).
   - The perception note uses native 100% (`round3/W1_perceived_high.md:26`). The baselines use 67%.
4. **Does "not reliably preferred over High" count as meeting the look target?**
   - Proposed test: in a pre-registered blind panel, the upper bound on the share preferring High is at most 63% (0.5 JOD). This is the label from `round4/R4_gpu_perception.md:196`.
   - It is weaker than "indistinguishable", which needs about 155 two-alternative trials (`round3/W1_perceived_high.md:20`).
   - The claim would be labelled "Medium-plus, not reliably preferred over High", never "High". The 45 fps track would keep being reported.
5. **The panel.**
   - The cheapest defensible design (`round4/R4_gpu_perception.md:186-193`):
     - 12 observers × 16 clips × 2 trials, about 20 minutes each;
     - controls: 4 High-vs-Low and 4 High-vs-High clips.
   - Fede can't be one of the confirmatory observers (`round3/W1_perceived_high.md:30`).
   - Open question: is it acceptable to show game captures to friends? (`round3/W1_perceived_high.md:132`). This is a licence question, and this note is not legal advice.
6. **The tier scheme.** Adopt the S0/S1 split into CLAUDE.md or not? This decides whether V2 can ever touch an anti-cheat game. It overlaps PR #8's open decision U8.
7. **Wukong's EULA.**
   - Section 8.3 defines a cheat as any external program that impacts gameplay, "simulating user operations, modifying operational environments, and altering data". §2.2 and §8.2(4) ban derivative works, including for non-profit purposes.
   - Doing this only for yourself lowers the copyright risk. It does not lower the contract risk (`round3/W5_ecosystem_upstream.md:174-183`).
   - Run V1's config-file work on Wukong anyway, or lead with Stalker 2?
8. **Send the vendor letters?** The X4 template in `round2/X_anticheat_legal_maint.md:139-142` goes to Focus/Saber (Space Marine 2) and Arrowhead/Sony (Helldivers 2). If there is no answer within 14 days, the item stays excluded for that game.

---

## 4. What a stock Deck already does

Most round-1 ideas turned out to be already shipped, already done inside the engine, or smaller than claimed. This table is the most reusable result of the study.

| Round-1 idea | Already true on a stock Deck | Source |
|---|---|---|
| Driver-forced variable-rate shading | SteamOS's **"Half Rate Shading"** toggle uses `RADV_FORCE_VRS_CONFIG_FILE`; `RADV_FORCE_VRS` is ignored. The forced rate skips mesh shaders, discarding or FragCoord-reading shaders, full-screen and UI draws, and all compute. What remains is about 0–1.4 ms in UE5 and 0 in Alan Wake 2 (est.). | `round2/X_anticheat_legal_maint.md:14`; `round2/A_G_vrs_reprojection.md` |
| Restoring Wine thread priorities | `* hard nice -8` has been set since at least February 2024 | `round2/C_sched_power.md` |
| Huge pages | THP=always is the kernel default | same |
| Faster sync primitives | Proton 11 uses ntsync by default. `PROTON_NO_NTSYNC=1` falls back to fsync. | `round3/W3_cpu_wall.md`; `round4/R4_cpu_ecosystem.md` §3 |
| Hand-found translation-layer fixes | vkd3d-proton's Wilds `no_upload_hvv` and its UE workarounds are on by default | `round2/E_F_search_autotune.md` |
| Running Lumen every few frames | UE5 already budgets Lumen's surface cache per frame, caches VSM shadows, and renders clouds temporally at 1/16 pixel | `round2/B_H_amortization_gi.md` |
| A dot4 neural upscaler | XeSS DP4a already uses `v_dot4_i32_i8` on the Deck, at about 557×348 from 800p | `round2/D_neural.md` |
| Per-game power profiles | Valve's steamos-manager manages CAPPED/UNCAPPED. SimpleDeckyTDP and PowerTools cover TDP, governor, SMT and clocks. | `round2/C_sched_power.md`; `round2/X_anticheat_legal_maint.md` |

---

## 5. The walls, with numbers

- **W1: what "High" means on this screen.**
  - At 30–40 cm the Deck shows 42–56 pixels per degree, about the same as a desktop monitor. So "the small screen hides it" is weaker than intuition suggests.
  - Nobody has measured any target game at the High preset near 800p. Every "High-like" fps figure here is an estimate: a measured Low or Medium point multiplied by a measured PC preset ratio (`round2/baselines_stack.md`).
  - Perceptual metrics judge rendering artifacts poorly. ColorVideoVDP scores PLCC 0.744; CGVQM-5 scores 0.871 but only on its own dataset (`round4/R4_gpu_perception.md` §7). So humans decide, and a small panel is not enough.
- **W2: GPU work that doesn't shrink with resolution.**
  - It is 34–66% of the frame (est.). One clean Wukong pair at Low puts it at 64%.
  - TSR on a Deck measured about 2.6 ms at 360p→720p (an Epic forum post by a developer optimising for the Deck; model unstated). That suggests about 2.0–2.9 ms at 800p.
  - Whether the round-2 High-like baselines already include that cost is unconfirmed (`verification/verifier_round1.md`, "Unconfirmed").
- **W3: CPU-bound scenes.**
  - Space Marine 2 hordes are limited by core count.
    - A launch-week Deck review saw drops to 14 fps (`round2/baselines_stack.md:33`). Round 4 calls that one anecdote.
    - Scaling from the PS5 suggests about 18 fps in the worst hordes (est.). Current horde fps has not been measured.
    - S0/S1 levers reach about 1.15× at best (`round4/R4_cpu_ecosystem.md`, SM2 verdict).
  - Stalker 2 settlements are CPU-bound on PC.
  - The two round-3 notes disagree on whether the Wilds plains are CPU- or GPU-bound. §9 step 6 settles it.
- **W4: reconstruction without matrix cores.**
  - Per-game neural upscalers are dead. Training per game buys only about 0.1–0.3 dB over game-generic training.
  - INT4 isn't reachable through Vulkan on stock Mesa.
  - AMD has committed FSR 4 for RDNA2 desktop cards in early 2027, not for the Deck.
- **W5: maintenance by a non-engineer.**
  - SteamOS's root filesystem is read-only and overwritten by updates.
  - `/etc` edits need an `/etc/atomic-update.conf.d` drop-in to survive.
  - Custom Mesa, gamescope or Proton builds lose Valve's shader pre-cache and raise anti-cheat risk.
  - Durable means config-only, or upstream.
- **Legal and contract** (not legal advice).
  - The Wukong EULA (§3, decision 7) and Capcom's EULA, which bans "analyzing… data" (§8.1), bind regardless of how private the use is.
  - REFramework, which every Wilds mod route needs, bypasses RE Engine's integrity checks, and that part can't be switched off (`round4/R4_gpu_perception.md`, verification point 2).
  - Game captures and raw frames stay on the bench and never go to Claude, CI or the cloud.

---

## 6. The ideas, scored against the viability test

"Viable" means all six of these hold:

1. not already shipped;
2. survived sceptic review in at least two rounds;
3. inside the legal lines and the current CLAUDE.md tiers;
4. an expected central gain at or above its own pass bar;
5. a falsification experiment of two weeks or less, judged by a measurement;
6. something a non-engineer can keep alive.

| | 1 new | 2 reviewed | 3 legal/tier | 4 gain | 5 test | 6 maintainable | Result |
|---|---|---|---|---|---|---|---|
| V1 | ✓ | ✓ (R2, R4) | ✓ for settings files; Wukong contract caveat | ✓ against its own test (central +0.3 JOD / 8–12% ms, vs a pass bar of ≥0.3 JOD with ≥58% preference and a kill below 5% saved, `round2/E_F_search_autotune.md:37,112-113`). ✗ against the separate Wukong 30-lock target (central 2.5 ms vs ≥4.3 ms needed). | ✓ | ✓ | **Viable** as an idea; not the Wukong lock |
| V2 | partly | partly (the 1100 MHz pin was reviewed in R4 only) | ✓ for non-anti-cheat games; anti-cheat pending §3.6 and §3.8 | ✗ central p99 −5% vs its own ≥8% bar | ✓ | partly (Steam rewrites values) | **Conditional** |
| V3 | ✓ | ✓ (R2, R4) | ✓ | unknown (depends on third parties) | ✗ judged by a maintainer acting within 60 days | ✓ | **Conditional** |
| V4 | ✓ | ✓ (R2) | ✓ inside gamescope | not native | ✓ offline test | ✗ unless Valve adopts it | Complementary |

**Why the loop stopped at four rounds, short of three viable ideas.**
1. Rounds 3 and 4 mostly produced knobs that fold into V1, or small items. The paper search is giving diminishing returns.
2. The facts that would promote or kill the conditional ideas can only come from a bench Deck:
   - the real High baseline;
   - the fixed-cost share;
   - whether a panel accepts Medium-plus;
   - whether the Wilds plains are CPU-bound;
   - whether V2's p99 gain reaches 8% at 15 W.
3. The remaining gap is game-side content.

So the next useful iteration of the loop is empirical (§9). Another paper round is possible if Fede wants one. It would need new inputs, such as a publisher contact or a Deck capture, to avoid repeating itself.

### V1. Deck "perceived-High" profiles (current Tier S: in-game settings files)

**What it is.** A per-game profile written only to the user's own settings and config files, through `deckforge.safety` (R10). It is found by measuring on a bench Deck, and kept only if a blind panel does not reliably prefer High over it.

**Why it's new.** Human Deck guides exist. But no existing tool does any of these (`round2/X_anticheat_legal_maint.md` §4):
- prices settings at the Deck's own 15 W and viewing geometry;
- searches the Unreal cvars that sit below the presets;
- re-runs automatically after a game patch.

**Knobs.** They all sit under one umbrella. Never add their savings together (`round4/R4_gpu_perception.md:236`). The knob notes are `round3/W1_perceived_high.md`, `round3/W2_W4_gpu_fixed_cost.md` and `round4/R4_gpu_perception.md`.
- menu settings;
- render scale × upscaler (TSR, FSR, XeSS);
- Lumen budget cvars;
- the irradiance-field-gather probe;
- TSR history size and split reconstruction;
- texture mip bias;
- effect density held at display resolution;
- motion blur;
- Steam's Half Rate Shading toggle;
- for Stalker 2, a CPU column of animation and LOD cvars.

**Budget (est.).**

| Comparison | Pessimistic | Central | Optimistic |
|---|---|---|---|
| Against the nearest stock preset at equal look (`round2/E_F_search_autotune.md:37`) | 3% | 8–12% | 20% |
| Against the best existing human Deck guide | 0% | 0–5% | 10% |
| Medium-plus Wukong. The note's own itemisation is 3–4 ms in total (`round3/W1_perceived_high.md:119`). My estimate sums Lumen budgets (~1 ms, half of `round2/B_H_amortization_gi.md:42`), split reconstruction 0.6 and FSR mip bias 0.4 (`round4/R4_gpu_perception.md:50,132`) and the driver sweep 0.45. These knobs overlap, so **my estimate is likely high**. | 0.5 ms | 2.5 ms | 5 ms |

**Where it's aimed.**
- **Wukong:** it has a free, deterministic benchmark tool, and Medium/50% is the closest to a lock. Subject to §3, decision 7.
- **Stalker 2:** the alternative lead.
- **Space Marine 2:** raise its GPU settings up to the CPU-bound line. Its game settings file is current Tier S. Risk is low (est.), pending Focus/Saber's answer, because its "Mods Detected" gate could misfire on config edits (`round2/X_anticheat_legal_maint.md:170`).

**Judges.** V1 as an idea is judged by its own test: at equal Deck ms, it must beat the nearest stock preset by ≥0.3 JOD with ≥58% panel preference (`round2/E_F_search_autotune.md:112-113`). That comparison is in §9 step 5. The Wukong lock in step 4 is a separate, harder target. The judges for both:
- Frame time: at least 5 runs, 95% confidence intervals, against the locked-30 definition in §3, decision 2.
- Look: the pre-registered panel (§3, decision 5).
- ColorVideoVDP, with a measured Deck display model, plus CGVQM: these only *rank* candidates.

**Keeping it alive.** Re-validate after each game patch on the bench. No binaries are touched.

**Risks.**
- Shipping builds may ignore cvars, so every knob gets a visible-extreme check first.
- The benchmark tool is a frozen build, so the drift that matters is SteamOS and Proton, not game patches.
- The irradiance-gather probe may render wrong lighting rather than crash, so compare against High.
- The Wukong contract (§3, decision 7).

### V2. Stutter kit (proposed S0; not current Tier S)

**What it is.** A bundle of system-level changes, A/B-tested together. Sources: `round2/C_sched_power.md`, `round3/W3_cpu_wall.md` and `round4/R4_cpu_ecosystem.md`.

- **CPU power mode:** the kernel's "guided" frequency mode (`amd_pstate=guided`), or EPP=performance on both siblings of the critical cores.
  - LPC 2026 slides, Civ VI on a Deck OLED: worst-1% frame time went from 70–73 ms to 47 ms, and p999 from 75–77 ms to 51 ms. Rendering power went from 12.09 to 12.20 W (n=3).
  - These were measured **on the charger, not at a binding 15 W cap.**
- **Scheduler slice:** `base_slice_ns` from 2.8 ms down to 0.3–0.7 ms. It reverts on suspend unless it is written before `tunable_scaling`.
- **Thread priorities:** SCHED_IDLE for decompression and IO workers only.
- **Space Marine 2, CPU-bound scenes only:** a GPU clock pin of about 1100 MHz.
  - Applies only if the power-limit throttle bits fire, and auto mode doesn't already drop the GPU below 1200 MHz.
  - Steam's Manual GPU Clock sets a pin, not a ceiling.
  - Gated on §3, decisions 6 and 8.
- **Checked undervolt:** Fede changes BIOS voltage offsets himself. DeckForge validates them with checksum kernels, cold and warm.
- **Throttle-bit logging:** decides whether any power lever can matter at all.

**Diagnostic, before any arm.**
- A sampler reads `/proc/<pid>/task/*/schedstat`, `gpu_metrics.average_gfx_activity` and thread names, from outside the game.
- An "auto vs 1100 MHz pin" elasticity arm separates CPU-bound frames from GPU fixed cost.
- Don't use fdinfo `drm-engine-gfx`: it counts ring occupancy and can exceed wall time.

**Budget (est.).**

| Measure | Pessimistic | Central | Optimistic |
|---|---|---|---|
| p99 frame time in CPU-bound hubs | 0 | −5% (**below its own pass bar**) | −25% |
| Average fps, CPU-bound scenes | 0 | +3% | +8% |
| Average fps, GPU-bound scenes | −1.5% | 0 | +1% |

This targets stutter, not the gap to High. The GPU-bound pessimistic case would fail the −1% guard below, and the A/B test exists to catch that.

**Judge.** Interleaved ABAB runs at 15 W.
- **Pass:** p99 at least 8% better in 2 or more target scenes, average fps no worse than −1% in GPU-bound scenes, and energy per frame up by no more than 5%.
- **Kill:** p99 better by less than 3% everywhere.
- **Positive control:** Civ VI in the guided CPU mode **on the charger**, as LPC measured it. It must show a worst-1% improvement of 20% or more. The 15 W run is the actual test.

**Risks and undo.**
- **The undervolt can silently corrupt data, including save files** (`round2/C_sched_power.md:112`). Two rules follow:
  - **Back up the game save folders before the first undervolt run.** Resetting the BIOS does not repair corruption that has already been written.
  - The undervolt must pass the checksum validation, with a 10 mV margin, before any real play.
- **Undo:**
  - a reboot resets the kernel and sysfs values;
  - BIOS offsets are reset in the Setup Utility;
  - `/etc` drop-ins are written and removed through `deckforge.safety`'s manifest (R10);
  - Steam rewrites some values, so each one is read back every second.
- **Excluded:**
  - `mitigations=off` is research only and never shipped, because the Deck runs a web browser.
  - Only `spectre_v2_user=off` could ever be recommended, and only if it alone carries a measured gain.

### V3. Upstream and publisher evidence channel (no code on the Deck)

**What it is.** Bench measurements turned into changes that other people ship. It costs Fede nothing to maintain.

**Items, in order:**
1. **SteamOS issue.**
   - The problem: `steamos-cfs-debugfs-settings` makes 3 writes to files that Linux 6.6 removed, and logs a false failure on every boot. Its `migration_cost_ns` and `nr_migrate` writes still work.
   - Separately: any `base_slice_ns` write reverts on CPU hotplug, which is upstream behaviour since 5.13. S3 ("deep") suspend triggers it; s2idle doesn't. An LCD Deck log shows deep; the OLED's mode is unverified.
   - The fix is to drop the dead writes, and to set `base_slice_ns` then `tunable_scaling` if a shorter slice is wanted.
   - File only after §9 step 2 confirms the predictions (`round4/R4_cpu_ecosystem.md` §8, which also lists the wording fixes).
2. **Per-game entries** in vkd3d-proton's `device_workarounds.c` or Mesa driconf, where V1's or V2's sweeps find a stock-config win.
   - Since 2026-09-08 vkd3d-proton forwards the game's engine to the driver, so engine-wide entries are possible.
3. **A one-day census** of `RtlGetDeviceFamilyInfoEnum` callers.
   - Wine and Proton report "unknown device", so games can't detect a handheld through it.
   - Expected value is about 0, because games like DOOM: The Dark Ages already autodetect the Deck.
   - Pursue only if 2 or more of 10 titles call it from game code.
4. **Publisher asks, sent through Valve first. Long shots** (est.: Capcom replies to under 5% of individual packets; Valve 10–20%):
   - Capcom: expose Wilds' Switch 2 content tier (out 4 Dec 2026) on PC behind `SteamDeck=1`.
     - This would raise the floor at a below-High look. It does nothing for High-like.
     - Only if §9 step 6 shows the plains are CPU-bound, and after Digital Foundry's Switch 2 analysis.
   - Focus/Saber: a swarm and AI budget for 4-core CPUs under `SteamDeck=1`.
   - Precedents for per-game Deck presets (FF7 Rebirth, Satisfactory, DOOM: The Dark Ages, Death Stranding 2, Space Marine 2's `SteamDeck=1`) came from Verified reviews and handheld launches, not from petitions.

**Realistic yield (est.).** About 1–3 items a year that a maintainer acts on. The KPI is "a maintainer acted". Kill the channel if none of the first 3 packets is acted on within 60 days.

### V4. Smoothness track (presented fps, not native)

- **Camera re-aiming between frames.** A first-person rotation warp, latched to the latest input, inside gamescope.
  - Pitch it to Valve rather than fork gamescope.
  - It costs 2.5–6.5% of native fps (est.).
  - Orbit cameras likely shimmer around the character, so an offline PC test decides them first (`round2/A_G_vrs_reprojection.md`).
- **lsfg-vk frame generation** on top of a native 30.
  - It is Tier I (an in-process Vulkan layer), so not for anti-cheat games.
  - Since its move to CC BY-NC-ND 4.0, DeckForge can point users to it but cannot bundle it.

---

## 7. Per-game outlook (all estimates, against unmeasured High baselines)

| Game | High-like today | V1 + driver sweep at a High-preset look (pess / central / opt) | Medium-plus route | What could close the rest | Tier notes |
|---|---|---|---|---|---|
| Black Myth: Wukong | ~18.5 fps | 19.1 / 20.9 / 24.1 fps | Measured 32 avg / 28 at the 5th-percentile low at Medium/50%. After V1: 35–37 fps average on the note's 3–4 ms estimate, and 32.5 / 34.8 / 38.1 fps on my estimate (likely high). **Borderline to unlikely lock** on paper (below). | A panel accepting Medium-plus, plus the bench beating the paper estimate | Settings files; EULA §8.3 (§3, decision 7) |
| Stalker 2 (v2.0, UE 5.5.4) | ~18.7 fps | 19.3 / 21.1 / 24.3 fps | Unknown: no v2.0 Deck measurement | Measure first; CPU column for settlements | No anti-cheat; Tier I possible |
| Monster Hunter Wilds | ~15 fps | About 15.4 fps. Only the 3% pessimistic case applies: the central and optimistic cases assume UE-style cvars Wilds doesn't have (`round2/E_F_search_autotune.md:31`). | Verified "30 and above most of the time" at defaults; plains below 20 | Long shot: a Capcom handheld tier at a below-High look (V3) | Menu only; Tier I dead |
| Space Marine 2 | ~22 fps average. Hordes: drops to 14 fps seen at launch (one review); ~18 in the worst hordes by PS5 scaling (est.); current figure unmeasured. | Near-High graphics at today's fps, if the CPU limit is simulation. Hordes 0 / +3 / +15% for the whole V2 stack (the GPU pin alone is 0 / +3 / +8%), pending §3.6 and §3.8. | n/a | Saber's 4-core swarm budget (V3) | Easy Anti-Cheat |
| Alan Wake 2 | ~11 fps | ~11 fps (the non-mesh-shader probe is −3 / 0 / +2 ms) | n/a | Not reachable with these levers | No anti-cheat (Epic store) |

**How these were computed** (my arithmetic, est.). The verifiers recomputed every row independently and got the same figures:
- `verification/arith2.py.txt` and `verifier_round2.md` checked the rows;
- `verification/check3.py.txt` and `verifier_round3.md` checked the 35–37 fps figure and the benchmark-tool bar.

High-preset look:
- frame time = baseline × (1 − V1 %) × (1 − driver-sweep %);
- V1 at 3 / 10 / 20% (`round2/E_F_search_autotune.md:37`);
- driver sweep at 0 / 1.5 / 4% (`round2/E_F_search_autotune.md`, F2);
- Half Rate Shading is inside V1 and not added again;
- baselines: Wukong 54 ms, Stalker 2 53.5 ms, Wilds 67 ms (`round2/baselines_stack.md`);
- the CPU levers add about 0 here because these scenes are GPU-bound.

Medium-plus Wukong:
- 31.25 ms measured, minus either the note's 3–4 ms or my estimate of 0.5 / 2.5 / 5 ms (likely high).
- A locked 30 under the §3.2 definition needs an uncapped p99 of 31.7 ms or less. In gameplay, 1% lows run 0.75–0.85× the average (`round2/baselines_stack.md`), so that needs an average frame time of about 23.8–26.9 ms. That is a saving of about 4.3–7.5 ms.
- The note's top figure, 4 ms, falls just short of even the easy end, 4.3 ms. My 5 ms reaches it only when 1% lows are good (ratio 0.85) (`verification/arith2.py.txt`).
- **Benchmark tool versus gameplay.**
  - A note puts lows at about 0.90× the average in the benchmark tool (`round2/baselines_stack.md:104`, "optimistic"). At that ratio the bar would be about 2.7 ms.
  - But the measured 28 fps at the 5th percentile against a 32 fps average already puts the ratio at or below 0.875. That makes the bar about 3.5 ms or more (`verification/check3.py.txt`).
  - Either way, a lock shown only in the benchmark tool is provisional. Gameplay decides.
- If XeSS is needed to pass the panel, it costs about 1.5 ms more (est.), which makes this harder.

The baselines are estimates. §9 step 1 replaces them with measurements.

---

## 8. Research-gated ideas and what died

**Gated.** Each has a cheap test, but its expected value is low or it depends on someone else:
- **Generic Deck-budget INT8 temporal upscaler.**
  - Frozen until AMD's RDNA2 FSR 4 ships, and dead if that runs in 3 ms or less on a Deck.
  - Meanwhile, XeSS at a lower internal resolution is tested inside V1.
- **Local, per-user harvested GI.** Only for games whose EULA allows it (Stalker 2 and Alan Wake 2, both unverified), and never distributed.
- **Tier I subgraph skip.** One curated rendering step in one non-UE game without anti-cheat, run under validation layers.
- **Alan Wake 2's non-mesh-shader path** (`VKD3D_DISABLE_EXTENSIONS=VK_EXT_mesh_shader`). One evening. The prior reports are mixed.
- **Lock-in cvar pricing via UE4SS.** Bench-only, Tier I. Its realistic standard error is about 0.3 ms, not 0.05.
- **Profiles chosen by the ambient-light sensor.** Lowest priority. Only if a 2-week log shows at least 20% of play time outside the default lighting bucket.

**Dead.**

| Idea | Why it died | Where |
|---|---|---|
| Blanket forced VRS | Already ships as Half Rate Shading | `round2/X_anticheat_legal_maint.md:14` |
| Per-pipeline VRS policy | Its targets are excluded for correctness; would need a Mesa patch | `round2/A_G_vrs_reprojection.md` |
| Blind Vulkan-layer pass skipping | Barriers carry no dataflow, so skipping corrupts state | `round2/B_H_amortization_gi.md` |
| Far-cascade shadow division; exact memo | UE5 uses VSM; hashing costs as much as it saves | same |
| Per-game neural upscaler | Training per game adds only about 0.1–0.3 dB; XeSS already sits at that operating point | `round2/D_neural.md` |
| Low→High compositor filter | The preset differences are non-local | same |
| Per-frame power predictor | The firmware estimator works on about a 1 s timescale | `round2/C_sched_power.md` |
| Watt arbitrage in GPU-bound scenes | The CPU already draws only 2–3 W there | same |
| Custom Mesa, gamescope or Proton builds as a product | Anti-cheat risk, loss of the shader pre-cache, read-only root filesystem | `round2/X_anticheat_legal_maint.md` |
| Mesa SPIR-V shader replacement as Tier S | It rewrites the game's code, so it is Tier I; it is also silently skipped when the cache is warm | `round2/E_F_search_autotune.md` |
| Distributing harvested lighting or per-game weights | Derivative-work risk (*Micro Star v. FormGen*); EULAs | `round2/X_anticheat_legal_maint.md` |
| Any Wilds mod route | REFramework's integrity bypass is mandatory | `round4/R4_gpu_perception.md` |
| USB NPU, eGPU, Peltier cooler, higher TDP by BIOS mod | No PCIe over USB-C; the clock cap binds first; not shippable | `round1/5_power.md`; `round3/W5_ecosystem_upstream.md` |

---

## 9. First experiments (about three weeks on one bench Deck)

**Who does what.** A dev session never touches a real Deck (R7). Steps marked **manual** are Fede using his own Deck from a checklist. Steps marked **needs bench runner** wait until that runner exists, because they need scripts on the Deck. Space Marine 2 is excluded from every step until §3 decision 8 gets a written answer.

0. **Decisions and letters** (manual, 1 hour).
   - Answer §3.
   - Send the X4 letters.
1. **Wukong baseline** (manual, one evening).
   - Stock presets only: no config edits, no clock changes.
   - At 15 W, 3 runs each, with frame-time logs:
     - (a) High at 67% TSR. This will be the first High measurement near 800p.
     - (b) Medium at 50%, with FSR and with XeSS.
     - (c) Steam's Half Rate Shading on and off.
   - This recalibrates §7.
2. **System check** (manual, 1 hour).
   - First, read only: `base_slice_ns`, `migration_cost_ns`, `nr_migrate`, `/sys/power/mem_sleep`, `amd_pstate/status`, the game process's nice limit, and the journal line "Not all CFS debugfs settings applied".
   - Then two writes on the bench Deck:
     - write 300000, suspend for 5 minutes, re-read;
     - repeat with `tunable_scaling` written afterwards.
   - **Expected:** 2800000 / 50000 / 128 / `[deep]`; the plain write reverts; the two-step write holds.
   - If all of that holds, Fede files the corrected V3 issue.
3. **Fixed-cost fit** (4 days; GPU traces need the bench runner).
   - The resolution axes use Wukong's own menu settings.
   - The pinned-clock arms (1.0 vs 1.6 GHz) and the `MESA_VK_TRACE=rgp` traces run on Stalker 2, to stay clear of Wukong §8.3 (`round4/R4_cpu_ecosystem.md:51`).
   - Classify passes by per-pipeline regression.
   - **Result:** a scene-fixed share of 40% or more means W2 is large; under 25% means small.
4. **V1 knobs on Wukong or Stalker 2** (manual config edits plus runs, 1 week; per §3, decision 7).
   - Test each knob alone, confirmed live by a visible extreme value, then combined.
   - The irradiance-gather probe is compared against High, not just checked for a crash.
   - Copy each config file before editing it.
   - **Pass:** the locked-30 definition from §3 decision 2, measured directly at Medium-plus in pre-registered gameplay scenes (in practice, a saving of at least about 4.3 ms), with no more than 0.25 JOD loss on the metric screen.
     - A pass in the benchmark tool alone is labelled provisional, because its lows run about 0.90× (`round2/baselines_stack.md:104`).
   - **Kill:** less than 2 ms saved.
   - **Between 2 and 4.3 ms saved:** V1 survives as a profile idea, but not as the Wukong lock. Judge it on its own test in step 5.
5. **Panel pilot** (manual, in parallel; needs §3 decision 5).
   - 8 observers.
   - Wukong clip pairs:
     - High vs Medium-plus;
     - **stock Medium vs the V1 candidate at equal Deck ms**: this is V1's own test, which passes at ≥0.3 JOD and ≥58% preference;
     - controls: High vs Low, and High vs High.
   - **Instrument kill:** High vs Low below 1 JOD, or High vs High outside 40–60%.
   - Then the 12×16×2 confirmatory panel, which Fede does not sit in.
6. **V2 bundle** (needs bench runner, 1 week).
   - Triage, with Civ VI and a GPU-bound control on a game without anti-cheat.
   - Then the arms on a Stalker 2 settlement, plus the charger-based Civ VI positive control.
   - **Wilds plains question:** Windward Plains at Lowest, internal 360p vs 800p, 10 runs, frame-time logs only.
     - Under 10% change means CPU-bound, so draft the Capcom packet.
     - Over 25% means GPU-bound, so drop it.
     - Contract note: Capcom §8.1 bans "analyzing… data". Whether frame-time logging counts as that is untested (`round4/R4_cpu_ecosystem.md:119`). Fede's call; not legal advice.

**What Fede does by hand:**
- answer the §3 decisions and send the letters;
- install the games and the benchmark tool;
- run the manual steps;
- set the BIOS undervolt offsets when asked;
- tape-measure his viewing distance;
- recruit the panel;
- file the issues once drafted.

The panel's reference frames are rendered on his Windows PC and stay on his machines.

---

## 10. Unknown unknowns worth keeping

- **GPU ID collisions.** Microsoft's handheld tables swap the Ally and Ally X GPU IDs, and 0x163F is also the LCD Deck. So any preset keyed on GPU ID is ambiguous.
- **Frame-time quantisation.** The Deck has no VRR. Under FIFO, gains smaller than one refresh interval disappear from presented frame times, so measure from present timestamps.
- **Background CPU load.** Non-game processes (steamwebhelper, background `fossilize_replay`, mangoapp) may take 0.3–0.5 of a core in CPU-bound scenes.
- **Near-black on the OLED.** Depending on the brightness slider, it may hide or exaggerate High's deep-shadow GI. Measure a grey ramp before trusting the metric's display model.
- **Thermals.** The OLED's fan likely has headroom (est., `round3/W5_ecosystem_upstream.md`). Throttle-bit logs confirm whether thermal limits ever bind.

---

## 11. Limits of this study

- **Nothing here was measured by this project.** Every figure is someone else's published measurement (linked in the notes) or an estimate marked (est.).
- **Four load-bearing facts were checked against their sources by the author:**
  - the Wukong OLED benchmark thread;
  - Wilds on Switch 2 on 4 December 2026;
  - the LPC 2026 slides, including the charger caveat;
  - the Wukong EULA's §2.2, §8.2(4) and §8.3 text.
- **Not every source could be reached.** Some agents couldn't reach gitlab.freedesktop.org or some publisher sites; those items are marked [could not verify]. Local source copies the agents cite were temporary; the citations point to upstream commits and URLs.
- **Legal readings are cautious readings, not legal advice.** "Safe-likely" anti-cheat verdicts are inferences. The only way to be sure is the vendor's written answer, never a test on an account.
- **The notes are model output and contain errors.** Each review round found several errors in the round before it, and the verifiers found 13 errors in revision 1 of this document, 11 in revision 2 and 5 in revision 3. Treat every number as a hypothesis for the bench.
