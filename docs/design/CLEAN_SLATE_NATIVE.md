# Clean-slate search: playing demanding games natively on the Steam Deck

**Status:** research result, not a build plan. Nothing in this document has been measured on a Deck by this project.

**Dated:** 2026-10-18.

**Evidence:** the raw notes are in `docs/research/2026-10-18-clean-slate/`, with an index in its `README.md`. File references below such as `round2/C_sched_power.md` point into that folder.

---

## 1. The answer in plain words

Fede asked for a fresh start. The goal: find a way to play demanding (PS5-era) games natively on the Deck. The method: a team of sub-agents with different viewpoints, a loop until at least three ideas are viable, and no hiding behind "the hardware is too weak".

**The process.** Twenty agents ran in four rounds:
1. Seven specialists invented about 40 ideas.
2. Seven sceptics tried to break each idea and then rescue it.
3. Four new specialists attacked the specific walls that round 2 exposed.
4. Two fresh sceptics reviewed the round-3 ideas.

**What survived: three viable ideas, plus one complementary track.**

| # | Idea | What it does | Works with anti-cheat? |
|---|---|---|---|
| V1 | **Deck "perceived-High" profiles** | Config-file profiles per game, found by a measured search and judged by a blind panel on the Deck's own screen | Yes (user config only) |
| V2 | **Stutter kit** | CPU power mode, scheduler fixes and guided undervolt, applied from outside the game | Yes (outside the game process) |
| V3 | **Upstream and publisher evidence channel** | Turns bench measurements into fixes Valve, Mesa, Proton and publishers ship | Yes (nothing runs on the Deck) |
| V4 | Smoothness track (not native fps) | First-person camera re-aiming between frames, plus frame generation on top of a native 30 | Re-aiming yes if built into gamescope; frame generation (lsfg-vk) no — it is Tier I |

**The honest ceiling.** None of these closes the gap to "a locked 30 fps natively at the game's High preset" for any of the five target games, at the central estimate.

What is plausible:

- **Black Myth: Wukong** can probably hold a locked 30 fps at a "Medium-plus" look.
  - It measured 32 fps average and 28 fps at the 5th-percentile low, at Medium with FSR at a 50% render scale, on an OLED Deck, in its benchmark tool. That was a user report from August 2024; the game has been patched since.
  - The open question is whether a blind panel can tell that look from High on a 7" screen at hand-held distance. Nobody has tested it. V1's first experiment answers it.
- **Stalker 2** is similar but less certain: no current Medium measurement on a Deck exists.
- **Space Marine 2** is held back by the CPU in hordes. If its CPU limit is game simulation rather than render-thread work, it can run near-High graphics at today's frame rate for free; the triage in V2 tells which. Only the publisher can lift its horde floor to 30.
- **Monster Hunter Wilds** is limited to its own menu settings, because every mod route bypasses its anti-tamper. Its best lever is Capcom's Switch 2 version, out 4 December 2026.
- **Alan Wake 2** stays far from the target (about 11 fps at a High-like look, est.).

No game reaches 45 fps natively at a High-like look.

**Why "don't use hardware as an excuse" still ends here.**
- The PS5 has about 6.3× the Deck's GPU compute.
- Everything that can be changed from outside a game's code yields roughly 1.1–1.2× in the central case, and about 1.4× at best (est., section 7):
  - settings, driver, scheduler and power;
  - compositor;
  - upstream fixes.
- The rest of the gap sits inside the game's own content and code. Only the publisher can change that, which is why V3 exists.

Every wall was attacked from around, under and through. The rescue attempts are recorded in each note.

**Three decisions are Fede's** (section 3). The most important: would a blind-panel "perceived High" count as meeting the goal?

---

## 2. How the search ran

**The screenshot prompt.** Before the work started, Fede was given its four answers (in the conversation):
1. what a top professional would do that wasn't asked;
2. the rawest material to start from;
3. the methods and tools;
4. what external evidence would show the result is right.

He was also given the rewritten prompt. That prompt became the shared brief, `00_brief_round1.md`. Its main points:
- start from raw evidence: GPU captures, driver and kernel source, perception research;
- label every estimate;
- give every idea a falsification experiment of two weeks or less, judged by a measurement, not an opinion.

| Round | Agents | Viewpoints | Output |
|---|---|---|---|
| 1 | 7 | Console-port graphics, neural rendering, perception and display science, kernel/driver/compiler, power and thermal, offline precomputation, adjacent fields | About 40 ideas, clustered into A–I (`00_round2_clusters.md`) |
| 2 | 7 | One sceptic per cluster, an anti-cheat/legal/maintenance reviewer, and a baseline-and-stacking analyst | Verdicts, corrected budgets, measured baselines |
| 3 | 4 | Vision science and QA panels; UE5/RE Engine/Northlight engine programming; CPU profiling; ecosystem and upstream strategy | Ideas aimed at the five walls |
| 4 | 2 | Fresh sceptics with no earlier reasoning | Verdicts on the round-3 ideas |

**Rules every agent followed:**
- No DRM, anti-tamper or anti-cheat circumvention.
- No redistribution of game code or assets.
- No live streaming of frames. Data precomputed offline was allowed.
- Frame generation and reprojection never count toward native fps.

**Tiers, refined in round 2** (`round2/X_anticheat_legal_maint.md`):
- **S0:** outside the game process.
- **S1:** stock Valve binaries, changed only through documented environment variables or config files.
- **Tier I:** anything that replaces a binary or shader, or injects into the game.

Anti-cheat games get S0/S1 only.

---

## 3. Definitions, and the decisions only Fede can make

The repository currently holds three different targets:

| Source | Frame-rate target | Quality reference |
|---|---|---|
| `docs/QUALITY_TARGET.md` (2026-10-08) | median ≤22.2 ms (45 fps) | max settings at native 1280×800 |
| Fede, universal-feasibility request (PR #8) | 30 fps **without FSR or frame generation**; FSR and frame generation may lift it to 40+ | "on par with High settings" |
| This study's brief | ≥30 fps with good 1% lows; upscalers allowed because they run on the Deck; frame generation tracked separately | the High preset as perceived on the Deck's screen |

**Decisions needed:**
1. **Is an upscaler allowed in the native 30?**
   - Every estimate here assumes yes.
   - If no, as in the PR #8 wording, every target game falls further short. Wukong at Low with no upscaler isn't even measured.
2. **Does "looks like High to a blind panel at 30 cm" count as High?**
   - This is the one honest way the goal becomes reachable for Wukong.
   - Proposed wording, from `round4/R4_gpu_perception.md` §7: "not reliably preferred over High, with the upper bound of the preference for High at ≤63%, on a pre-registered clip set, at the panel's measured viewing distance".
   - The claim would be labelled "Medium-plus, perceived as High". It would never be called "High".
   - The 45 fps track keeps being reported, so the target isn't quietly lowered.
3. **Is he willing to run the panel?**
   - The cheapest defensible design is 12 observers × 16 clips × 2 trials: about 20 minutes per person, plus a 4-clip High-vs-Low control and a 4-clip High-vs-High control (`round4/R4_gpu_perception.md` §7).
   - His own blind A/B alone cannot settle it.

---

## 4. What a stock Deck already does

Most round-1 ideas were already shipped, already done inside the engine, or smaller than claimed. The table below is the most reusable result of this study.

| Round 1 idea | Already true on a stock Deck | Source |
|---|---|---|
| Driver-forced variable-rate shading | SteamOS's **"Half Rate Shading"** toggle drives `RADV_FORCE_VRS_CONFIG_FILE`. `RADV_FORCE_VRS` is ignored. The forced rate skips mesh shaders, discarding and FragCoord-reading shaders, full-screen and UI draws, and all compute. That leaves about 0–1.4 ms in UE5 games and 0 in Alan Wake 2 (est.). | `round2/A_G_vrs_reprojection.md` |
| Restoring Wine thread priorities | `* hard nice -8` has been set since at least Feb 2024 | `round2/C_sched_power.md` |
| Huge pages | THP=always is the kernel default | same |
| Faster sync primitives | Proton 11 uses ntsync by default. `PROTON_NO_NTSYNC=1` falls back to fsync. | `round3/W3_cpu_wall.md`, `round4/R4_cpu_ecosystem.md` §3 |
| Hand-found translation-layer fixes | vkd3d-proton's Wilds `no_upload_hvv` and its UE workarounds are on by default | `round2/E_F_search_autotune.md` |
| Running Lumen every few frames | UE5 already runs Lumen's surface cache on fixed per-frame budgets, caches VSM shadows, and has 1/16-pixel temporal clouds | `round2/B_H_amortization_gi.md` |
| A dot4 neural upscaler | XeSS DP4a already uses `v_dot4_i32_i8` on the Deck, at about 557×348 from 800p | `round2/D_neural.md` |
| Per-game power profiles | Valve's steamos-manager manages the CAPPED/UNCAPPED profiles. SimpleDeckyTDP and PowerTools cover TDP, governor, SMT and clocks. | `round2/C_sched_power.md`, `round2/X_anticheat_legal_maint.md` |

---

## 5. The walls, with numbers

- **W1: what "High" means on this screen.**
  - At 30–40 cm the Deck shows 42–56 pixels per degree. That is about the same as a desktop monitor, so "the small screen hides it" is weaker than intuition suggests.
  - No High-preset measurement near 800p exists for any target game. Every "High-like" fps figure here is an estimate: measured Low or Medium points times measured PC preset ratios (`round2/baselines_stack.md`).
  - Perceptual metrics are weak judges of rendering artifacts. ColorVideoVDP correlates at PLCC 0.744 on a rendering-artifact dataset; CGVQM-5 reaches 0.871, but within its own dataset (`round4/R4_gpu_perception.md` §7).
  - So humans must decide, and a small panel is not enough.
- **W2: GPU work that doesn't shrink with resolution.**
  - Its share is 34–66% of the frame (est.). One clean Wukong pair, at Low settings, puts it at 64%.
  - TSR on a Deck measured about 2.6 ms at 360p → 720p (an Epic forum thread by a developer optimising for the Deck, model unstated). That suggests about 2.0–2.9 ms at 800p, roughly twice the round-2 assumption.
  - A four-day three-axis fit settles the share (§9, step 3).
- **W3: CPU-bound scenes.**
  - Space Marine 2 hordes are core-count bound. From PS5 scaling, the worst hordes are about 18 fps on a Deck (est.). The S0/S1 stack credits at most about 1.15×.
  - Stalker 2 settlements are CPU-bound on PC. Wilds plains are disputed between the two round-3 notes (§9 step 6 decides).
- **W4: reconstruction without matrix cores.**
  - Per-game neural upscalers are dead: per-game training buys only about 0.1–0.3 dB over game-generic training.
  - INT4 isn't reachable through Vulkan on stock Mesa.
  - AMD has committed FSR 4 for RDNA2 desktop cards in early 2027, but not for the Deck.
- **W5: maintenance by a non-engineer.**
  - SteamOS's root filesystem is read-only and overwritten by updates.
  - `/etc` edits need an `/etc/atomic-update.conf.d` drop-in to survive an update.
  - Any custom Mesa, gamescope or Proton build loses Valve's shader pre-cache and raises anti-cheat risk.
  - Durable changes are config-only, or upstream.
- **Legal and contract** (not legal advice):
  - Wukong's EULA bans derivative works of data released into memory (§8.2(4)), and derivative works generally, "including for both for-profit and non-profit purposes" (§2.2). It also defines a cheat as any external program that affects operations during gameplay (§8.3).
  - Capcom's EULA bans "analyzing… data" (§8.1).
  - REFramework, which every Wilds mod route needs, bypasses RE Engine's integrity checks, and that part can't be switched off (`round4/R4_gpu_perception.md`, verification point 2).
  - Game captures and raw frames stay on the bench and never go to Claude, CI or the cloud.

---

## 6. The viable ideas

**"Viable"** here means all six of these hold:
1. not already shipped;
2. survived two independent sceptic rounds;
3. inside the legal lines and its claimed tier;
4. an expected gain that matters;
5. a falsification experiment of two weeks or less, judged by a measurement;
6. something a non-engineer can keep alive.

### V1. Deck "perceived-High" profiles (S1, config files)

**What it is.** A per-game profile written only to the user's own config files, through `deckforge.safety`. It is found by a measured search on a bench Deck and accepted only if a blind panel can't reliably tell it from High.

**Why it's new.** Human Deck guides exist, but nothing prices settings at the Deck's own 15 W and viewing geometry. Nothing searches the sub-preset Unreal cvars or re-runs automatically after a patch (`round2/X_anticheat_legal_maint.md` §4).

**Knobs.** They all sit under one umbrella; never add their savings together.
- the menu settings;
- render scale × upscaler (TSR, FSR, XeSS);
- Lumen budget cvars;
- the irradiance-field-gather probe (`r.Lumen.IrradianceFieldGather`);
- TSR history size (`r.TSR.History.ScreenPercentage`) and split reconstruction (`r.SecondaryScreenPercentage.GameViewport`);
- texture mip bias;
- effect density held at display resolution;
- motion blur;
- the Half Rate Shading toggle;
- for Stalker 2, a CPU column of animation and LOD cvars.

The knob notes are in `round3/W1_perceived_high.md`, `round3/W2_W4_gpu_fixed_cost.md` and `round4/R4_gpu_perception.md`.

**Budget (est.), saving against the nearest stock preset at equal look:**

| Case | Pessimistic | Central | Optimistic |
|---|---|---|---|
| UE5 at a High-like look | 3% | 10–12% | ~25% |
| Medium-plus Wukong | 1 ms | 3 ms | 6 ms |
| Wilds (menu only) | | ~10% plus Half Rate (est.) | |

Against the best existing human Deck guide, the gain is only 0–5% (`round2/E_F_search_autotune.md`).

**Where it is aimed:**
- **Wukong first.** It has a free, deterministic benchmark tool, and Medium at 50% is already close to a 30 fps lock.
- **Space Marine 2.** Raise the GPU settings to the CPU-bound line for free (an anti-cheat-safe config file).

**Judge.**
- Frame time: gamescope or mangoapp logs, at least 5 runs, 95% confidence intervals.
- Look: a pre-registered blind panel (§3, decision 3).
- Ranking candidates: ColorVideoVDP with a measured Deck display model, plus CGVQM.

**Keeping it alive.** Re-validate each game patch on the bench, which is automatable. No binaries are touched.

**Risks:**
- Shipping builds may ignore some cvars, so every cvar needs a visible-effect check.
- The benchmark tool is a frozen build.
- The irradiance gather may render wrong lighting instead of crashing, so compare the image against High.
- **Contract risk on Wukong** (not legal advice). Its EULA §8.3 defines a cheat as an external program that impacts gameplay, giving as examples "simulating user operations, modifying operational environments, and altering data".
  - A strict reading could reach both V1 and V2.
  - Bench work is Fede's personal use. Publishing Wukong profiles would want Game Science's non-objection first.

### V2. Stutter kit (S0, outside the game)

**What it is.** A small set of system-level changes, A/B-tested as one bundle on the bench:
- **CPU power mode:** `amd_pstate=guided`, or EPP=performance on both siblings of the critical cores.
  - LPC 2026 slides, Civ VI on a Deck OLED: worst-1% frame time went from 70–73 ms to 47 ms, and p999 from 75–77 ms to 51 ms. Rendering power went from 12.09 W to 12.20 W (n=3).
  - These were measured **on the charger, not at a binding 15 W cap.** Testing at 15 W is the gap DeckForge has to close.
- **Scheduler slice:** `base_slice_ns` from 2.8 ms to 0.3–0.7 ms. To make it survive suspend, write `base_slice_ns` and then `tunable_scaling`.
- **Thread priorities:** SCHED_IDLE for decompression and IO workers only.
- **Space Marine 2, CPU-bound scenes only:** a GPU clock pin around 1100 MHz. This applies only if the power-limit throttle bits fire, and only if auto mode doesn't already drop GFX below 1200 MHz.
- **Guided undervolt:** the user sets the BIOS offsets, and DeckForge validates them with checksum kernels, both cold and warm.
- **Logging:** throttle bits, which decide whether any power lever can matter.

The notes are `round2/C_sched_power.md`, `round3/W3_cpu_wall.md` and `round4/R4_cpu_ecosystem.md`.

**Why it's new.** Existing tools set TDP and governors. None targets the frame's critical threads. None found Valve's dead scheduler tunings, which round 4 confirmed.

**Budget (est.):**

| Measure | Pessimistic | Central | Optimistic |
|---|---|---|---|
| p99 frame time in CPU-bound hubs | 0 | −5% | −25% |
| Average fps in CPU-bound scenes | 0 | +3% | +8% |
| Average fps in GPU-bound scenes | ≈0 | ≈0 | ≈0 |

This fixes stutter, not the gap to High.

**Diagnostic, before any arm.** A root sampler at 10 Hz reads `/proc/<pid>/task/*/schedstat`, `gpu_metrics.average_gfx_activity` and thread names. Those reads come from outside the game process. It does not use fdinfo's `drm-engine-gfx`, which counts ring occupancy and so can exceed wall time. It also runs an auto-vs-pinned-1100 MHz elasticity arm. This tells CPU-bound scenes from GPU fixed cost.

**Judge.** Interleaved ABAB runs at 15 W.
- **Pass:** p99 at least 8% better in 2 or more target scenes, average fps loss no worse than −1% in GPU-bound scenes, and energy per frame up no more than 5%.
- **Kill:** p99 improves less than 3% everywhere.
- **Positive control:** Civ VI under guided mode must reproduce at least a 20% better worst-1%.

**Keeping it alive.**
- Steam rewrites some sysfs values, so each value is read back every second.
- `/etc` changes need the atomic-update drop-in.
- The kernel tunings should go upstream through V3.

**Excluded:**
- `mitigations=off` is research only and never shipped, because the Deck runs a web browser.
- Only `spectre_v2_user=off` could ever be recommended, and only if it alone carries a measured gain.

### V3. Upstream and publisher evidence channel (no code on the Deck)

**What it is.** DeckForge's bench measurements turned into changes other people ship, which costs Fede nothing to maintain.

**Concrete items, in order:**
1. **SteamOS issue.**
   - `steamos-cfs-debugfs-settings` makes 3 writes to files removed in Linux 6.6, and logs a false failure on every boot.
   - Its `base_slice` effect is undone by every CPU hotplug. This is upstream behaviour since kernel 5.13 moved these knobs to debugfs, under CFS too. S3 ("deep") suspend causes a hotplug and s2idle doesn't. An LCD Deck log shows deep; the OLED's mode is unverified.
   - Its `migration_cost_ns` and `nr_migrate` writes still work.
   - Fix the draft's wording first. The corrected text is in `round4/R4_cpu_ecosystem.md` §8.
   - File it only after the day-1 read-back check passes (§9, step 2).
2. **Per-game entries** in vkd3d-proton's `device_workarounds.c` (or Mesa driconf), wherever V1's or V2's sweeps find a stock-config win.
   - Since 2026-09-08, vkd3d-proton forwards the game's engine name to the driver. That makes engine-wide driver entries possible for the first time.
3. **A one-day census** of `RtlGetDeviceFamilyInfoEnum` callers.
   - Wine and Proton report "unknown device", so games can't detect a handheld.
   - Expected value is about 0, because games like DOOM: The Dark Ages already autodetect the Deck.
   - Pursue it only if 2 or more of 10 titles call it from game code.
4. **Publisher asks, sent through Valve first:**
   - Capcom: expose Wilds' Switch 2 content tier on PC behind `SteamDeck=1`. Wait for Digital Foundry's analysis of the Switch 2 version.
   - Focus/Saber: a swarm and AI budget for 4-core CPUs under `SteamDeck=1`.

**Precedents** of per-game Deck presets: FF7 Rebirth, Satisfactory, DOOM: The Dark Ages, Death Stranding 2, Space Marine 2's own `SteamDeck=1`. These came from Verified reviews and handheld launches, not from community petitions.

**Realistic yield.** About 1–3 items a year that a maintainer acts on (est.). KPI: "a maintainer acted". Kill the channel if none of the first 3 packets is acted on within 60 days.

### V4. Smoothness track: presented fps, not native

**What it is.**
- A first-person, input-latched rotation warp inside gamescope that re-aims the last frame on refreshes the game misses. It is pitched to Valve rather than forked, because a gamescope fork isn't maintainable by a non-engineer.
- Frame generation via lsfg-vk on top of a native 30.
  - It is Tier I (an in-process Vulkan layer), so not for anti-cheat games.
  - Its licence is now CC BY-NC-ND 4.0, so DeckForge can point users to it but cannot bundle it.

**Cost (est.).** The warp costs 2.5–6.5% of native fps. The latency gain is smaller than first claimed. Orbit-camera games likely shimmer around the character, so an offline PC test decides whether orbit cameras qualify at all (`round2/A_G_vrs_reprojection.md`).

---

## 7. Per-game outlook (all est., against unmeasured High baselines)

| Game | High-like today | V1+V2 central at a High-preset look | Medium-plus route | What closes the rest | Tier |
|---|---|---|---|---|---|
| Black Myth: Wukong | ~18.5 fps | ~21 fps (19–27) | Measured 32 avg / 28 at the 5th-percentile low at Medium/50%. About 33 / 35 / 40 fps average after V1 (est.), so a 30 lock is plausible. | The blind panel decides whether Medium-plus counts | S1 config; contract note on EULA §8.3 |
| Stalker 2 (v2.0, UE 5.5.4) | ~18.7 fps | ~21 fps in the wilderness | No current Deck Medium measurement | Measure first; CPU column for settlements | S1; Tier I possible (no anti-cheat) |
| Monster Hunter Wilds | ~15 fps | ~17.5 fps (menu + Half Rate) | Verified "30 and above most of the time" at defaults; the plains drop below 20 | Capcom's Switch 2 tier (V3) | Menu only (Tier I dead) |
| Space Marine 2 | ~22 fps average; worst hordes ~18 (est.) | Near-High graphics at today's fps (if the CPU limit is simulation); hordes 0 to +15%, central ~+5% | n/a | Saber's 4-core swarm budget (V3) | S0/S1 only (Easy Anti-Cheat) |
| Alan Wake 2 | ~11 fps | ~11–12 fps; the non-mesh-shader probe is −3 / 0 / +2 ms | n/a | Not reachable with these levers | Tier I possible (Epic store) |

**How the Wukong row was computed** (my arithmetic, est.). It starts from the round-2 High-like baseline of ~54 ms at 67% TSR → 800p.

| Case | V1 saving | Other savings | Frame time | fps |
|---|---|---|---|---|
| Pessimistic | 3%, 1.6 ms | — | 52.4 ms | 19.1 |
| Central | ~12%, 6.5 ms, including round 3's new knobs at their round-4 sizes | F's environment-variable sweep, 1.5%, 0.7 ms | 46.8 ms | 21.4 |
| Optimistic | ~25%, 13.5 ms | sweep 4%, 1.6 ms; Half Rate 1.4 ms | 37.5 ms | 26.7 |

- The CPU levers add ≈0, because the game is GPU-bound.
- **Medium-plus:** 31.25 ms measured, minus 1 / 3 / 6 ms, gives 33 / 35 / 40 fps average. A clean 30 lock needs about a 37.5 fps average, because 1% lows run 0.75–0.85× the average in gameplay (`round3/W1_perceived_high.md` Q3).
- Stalker 2 and Wilds were computed the same way, from 53.5 ms and 67 ms. For Wilds, Half Rate Shading counts 2.4 ms (RE Engine central, `round2/A_G_vrs_reprojection.md`).
- The baselines themselves are estimates, which is why §9 step 1 comes first.

---

## 8. Research-gated ideas (not counted as viable) and what died

**Gated. Each has a cheap test, but its expected value is low or it depends on someone else:**
- **Generic Deck-budget INT8 temporal upscaler.**
  - Frozen until AMD's RDNA2 FSR 4 ships.
  - Dead if that runs in ≤3 ms on the Deck.
  - Until then, test XeSS at a lower internal resolution inside V1.
- **Local, per-user harvested GI.** Only for games whose EULA allows it (Stalker 2 and Alan Wake 2, unverified). Never distributed.
- **Tier I subgraph skip.** One curated rendering step in one non-UE, non-anti-cheat game, under validation layers.
- **Alan Wake 2's non-mesh-shader path** (`VKD3D_DISABLE_EXTENSIONS=VK_EXT_mesh_shader`). One evening.
- **Lock-in cvar pricing** via UE4SS: bench only, Tier I. Its realistic standard error is about 0.3 ms, not 0.05.
- **Viewing-condition profiles from the light sensor.** Lowest priority; continue only if a 2-week log shows at least 20% of play time outside the default bucket.

**Dead, with the reason:**

| Idea | Why it died | Where |
|---|---|---|
| Blanket forced VRS | Already ships as Half Rate Shading | `round2/A_G_vrs_reprojection.md` |
| Per-pipeline VRS policy | Its targets are deliberately excluded for correctness; would need a Mesa patch | same |
| Blind Vulkan-layer pass skipping | Barriers carry no dataflow; skipping corrupts state | `round2/B_H_amortization_gi.md` |
| Far-cascade shadow division, exact memo | UE5 uses VSM; hashing costs as much as it saves | same |
| Per-game neural upscaler | Per-game training adds about 0.1–0.3 dB; XeSS already sits at that operating point | `round2/D_neural.md` |
| Low→High compositor filter | The differences between presets are non-local (shadows, GI, LOD) | same |
| Per-frame power predictor | The firmware estimator runs on about a 1 s timescale | `round2/C_sched_power.md` |
| Watt arbitrage in GPU-bound scenes | The CPU already draws only 2–3 W there | same |
| Custom Mesa, gamescope or Proton builds as a product | Anti-cheat risk, pre-cache loss, read-only rootfs | `round2/X_anticheat_legal_maint.md` |
| Mesa SPIR-V shader replacement as Tier S | It rewrites the game's code, so it is Tier I; it is also silently skipped when the cache is warm | `round2/E_F_search_autotune.md` |
| Distributing harvested lighting or per-game weights | Derivative-work risk (Micro Star v. FormGen); EULAs | `round2/X_anticheat_legal_maint.md` |
| Any Wilds mod route | REFramework's integrity bypass is mandatory | `round4/R4_gpu_perception.md` |
| USB NPU, eGPU, Peltier cooler, higher TDP via a BIOS mod | No PCIe over USB-C; the clock cap binds; not shippable | `round1/5_power.md`, `round3/W5_ecosystem_upstream.md` |

---

## 9. First two weeks: what to run, in order

Everything runs on a bench Deck driven by Fede or, later, the bench runner. A dev session never touches a real Deck (R7).

1. **One evening, no code: the real Wukong baseline.**
   - Run the Wukong benchmark tool at 15 W, 3 runs each, with frame-time logs:
     - (a) High at 67% TSR, the first High measurement near 800p anyone will have published;
     - (b) Medium at 50% with FSR and with XeSS;
     - (c) (b) with Half Rate Shading on.
   - This recalibrates every estimate in section 7.
2. **One hour, read-only: check the system.** Read:
   - `base_slice_ns`, `migration_cost_ns`, `nr_migrate`, `/sys/power/mem_sleep`, `amd_pstate/status`;
   - the nice limit on the game's process;
   - the journal line "Not all CFS debugfs settings applied".
   - Then write 300000, suspend 5 minutes and read it back. Then repeat with the persistence recipe. If the predictions hold, file the V3 issue.
3. **Four days: the fixed-cost fit.**
   - Wukong: 4 internal resolutions × 2 output resolutions × GPU clock pinned at 1.0 vs 1.6 GHz. Regress each pipeline's duration (GPU trace via `MESA_VK_TRACE=rgp`).
   - **Result:** a scene-fixed share of 40% or more means W2 is large; under 25% means small.
4. **One week: V1 knobs on Wukong.**
   - Each Engine.ini knob alone, confirmed live by a visible extreme value, then combined.
   - Includes a 10-minute irradiance-gather probe, compared against High, not just checked for a crash.
   - **Pass:** the combination saves at least 3 ms at Medium-plus with no metric loss over 0.25 JOD.
5. **In parallel: a panel pilot.**
   - 8 observers, Wukong clips: High vs Medium-plus, plus High-vs-Low and High-vs-High controls.
   - **Instrument kill:** High vs Low under 1 JOD, or High vs High outside 40–60%.
   - Then the 12×16×2 confirmatory panel.
6. **One week: the V2 bundle.**
   - Triage first, with Civ VI and a GPU-bound control.
   - Then the arms on a Space Marine 2 hub and a horde set-piece, and a Stalker 2 settlement, with the thresholds in §6 V2.
   - Plus one test for the Wilds dispute: Windward Plains at Lowest, internal 360p vs 800p, 10 runs. Under 10% change means CPU-bound, so send the Capcom packet. Over 25% means GPU-bound.

**What Fede does by hand:**
- install the games and the benchmark tool;
- start each run;
- set the BIOS undervolt offsets when asked;
- tape-measure his viewing distance;
- recruit and sit the panel;
- file the issues the runner drafts.

**Reference frames for the panel** are rendered on his Windows PC and stay on his machines.

---

## 10. Unknown unknowns worth keeping

- **GPU ID collisions.** Microsoft's handheld tables swap the Ally and Ally X GPU IDs, and 0x163F is also the LCD Deck. Any preset keyed on a GPU ID is ambiguous.
- **Quantised frame times.** The Deck has no VRR, so under FIFO, gains smaller than one refresh interval vanish in presented frame times. Measure from present timestamps.
- **Background CPU use.** Non-game processes (steamwebhelper, Steam's background `fossilize_replay`, mangoapp) may take 0.3–0.5 of a core in CPU-bound scenes.
- **Near-black on the OLED.** It may hide or exaggerate High's deep-shadow GI, depending on the brightness slider. Measure a grey ramp before trusting the metric's display model.
- **Thermal limits.** The OLED's fan has headroom, so thermal limits are unlikely to bind (`round3/W5_ecosystem_upstream.md`). Throttle-bit logs confirm it.

---

## 11. Limits of this study

- **No measurement by this project.** Every figure is a published measurement by someone else, with a link in the notes, or an estimate marked (est.).
- **Unverified items.** Several were checked by agents who could not reach gitlab.freedesktop.org or some publisher sites. They are marked [could not verify] in the notes.
- **Legal.** The readings in `round2/X_anticheat_legal_maint.md` and the round-3/4 notes are cautious readings, not legal advice.
- **Anti-cheat.** The "safe-likely" tier verdicts are inferences from published policy and precedent. The only way to be sure is to ask the vendor in writing (the X4 template in `round2/X_anticheat_legal_maint.md`), never to test on an account.
- **Quality of the evidence chain.** These notes are model output and contain errors. Each sceptic round found several in the round before. Treat every number as a hypothesis for the bench.
