# Round 2 red-team: clusters E and F

**Sources I read.**
- vkd3d-proton at commit `0bb64c56` (dated 2026-10-14), local clone in `scratchpad/src/vkd3d-proton`.
- Mesa main (VERSION 27.0.0-devel), through the GitHub mirror `chaotic-cx/mesa-mirror`. gitlab.freedesktop.org is blocked from this session. SteamOS's Mesa may be older than main.
- gamescope `main.cpp`.
- ColorVideoVDP (CVVDP) and FovVideoVDP READMEs.

---

## Cluster E: the perceptual price list

### E1. The core idea (per-game settings and cvar search)

**Is it already done? Mostly yes, by hand.**
- TechSpot's Wukong guide measured its "quality-optimised" settings at **−8% performance versus High**, with similar lighting and more world density. Its "performance" settings land between High and Medium ([TechSpot](https://www.techspot.com/guides/2884-wukong-optimization/)).
- Hand-made Deck ini packs and cvar packs already exist (for example, [Nexus Stalker 2 mods](https://nexusmods.com/stalker2heartofchornobyl/mods/561)).
- I could not find Digital Foundry figures against the *nearest* preset. Their guides quote gains against Ultra.
- This is consistent with the internal estimate of −8% to +8% for "same-look" settings.

**The "Deck viewing geometry" lever is weak.** My arithmetic:
- The Deck at 30–40 cm is 42–56 pixels per degree.
- A 27" 1440p monitor at 60 cm is about 45 ppd. A 24" 1080p monitor at 60 cm is about 38 ppd.
- So the Deck sits at desktop-guide geometry. Its screen does not reprice fine detail.
- What does differ: a 26° field of view (so peripheral effects matter less), 600–1000 nit peaks (artifacts *more* visible), and variable ambient light.

**Where a search could beat a human guide:**
- In UE titles (Wukong, Stalker 2), sub-preset cvars such as Lumen probe density or update factors fill the "Low is a cliff" gap below the presets. This is where the Deck lives.
- It is priced on the real 15 W Deck, per scene type (CPU-bound or GPU-bound).
- It re-runs automatically on every patch.
- The "hundreds of hidden cvars" argument applies to only 2 of the 5 target games. RE Engine, Swarm and Northlight expose a few config keys, not a cvar system.

**Gain range (est.):**

| Compared against | Pessimistic | Central | Optimistic |
|---|---|---|---|
| Nearest stock preset, equal Deck ms | +0.1 JOD / 3% ms | +0.3 JOD / 8–12% ms | +0.6 JOD / 20% (UE5 at a cliff) |
| Best existing human Deck guide | 0% | 0–5% | 10% |

- E is an umbrella. Render scale, VRS (cluster A), the UE update-rate cvars (B's Tier S part), motion blur and the upscaler choice are all items on its menu. **Do not add A or B's Tier S gains on top of E.**

**Metric validity:**
- **Deck display model:** yes, CVVDP can model it. Its display JSON takes `resolution`, `viewing_distance_meters`, `diagonal_size_inches`, `max_luminance`, `contrast`, `E_ambient`, `k_refl`, `colorspace` and `exposure`, loaded with `--config-paths` ([README:89–106,146–158](https://github.com/gfxdisp/ColorVideoVDP)) [checked]. Use the measured nits at the user's brightness slider and a measured `k_refl` (glossy and etched glass differ).
- **Foveation:** CVVDP has none. The Deck's 26° field makes this nearly irrelevant: the corners are about 15° from the centre. FovVideoVDP in its default non-foveated mode is equivalent. Don't assume a gaze point.
- **Rendering artifacts:** on Intel's CG-VQD rendering dataset (path tracing, upscaling with ghosting and flicker, VRS, frame interpolation):

  | Metric | PLCC | SRCC |
  |---|---|---|
  | CVVDP | 0.744 | 0.775 |
  | FovVideoVDP | 0.755 | 0.741 |
  | FLIP | 0.693 | 0.728 |
  | VMAF | 0.715 | 0.790 |
  | CGVQM | 0.871 | 0.877 |

  - CVVDP did best on VRS and poorly on frame interpolation, and it "overestimate[s] quality in high-distortion scenarios" ([arXiv 2506.11546](https://arxiv.org/html/2506.11546v1)) [checked].
  - TAA ghosting is not specifically in the dataset.
  - CVVDP's ML variants are calibrated on streaming distortions, not rendering ([metrics.md](https://github.com/gfxdisp/ColorVideoVDP/blob/main/metrics.md)).
- **Reference:** CVVDP is full-reference, so it needs pixel-aligned frames. Non-deterministic simulation plus frame-time-dependent sampling breaks alignment.
  - Rescue 1: UE `-Deterministic` = "`-UseFixedTimeStep -FixedSeed`" ([UE docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-command-line-arguments-reference)) [checked]. Whether shipping builds honour it: [could not verify].
  - Rescue 2: photo-mode stills. These are spatial only and flatter TAA.
  - Rescue 3: render the *quality* side on a PC at 1280×800 with identical settings and lossless capture, and measure only *ms* on the Deck. Lock the texture-streaming pool and dynamic resolution, or images diverge.
- **2AFC with 30 trials:** significance needs ≥20/30 correct. Power to detect a true 0.5 JOD effect (63% preference) is 0.43; for 0.3 JOD (58%) it is 0.22. 80% power needs about 87 trials for 0.5 JOD and about 238 for 0.3 JOD. A "<60%" kill rule at n=30 has a ±17.5 percentage-point 95% CI. **30 trials only detects ~1 JOD effects** (my binomial computation).

**Search cost.** The 125 Deck-hour figure is plausible only with group screening, not one-at-a-time testing.
- Most ini cvars need a relaunch; shipping consoles are locked.
- Single cvars are usually under 1% (0.2 ms), below Deck run-to-run noise (est. 1–3%).
- My budget per game, for one scene set with a benchmark tool:
  - screening 100 knobs: about 128 runs × 3 repeats × 4 min ≈ 26 h;
  - Bayesian optimisation on the top 15: about 150 × 3 × 4 min ≈ 30 h;
  - so **about 55 h central** (30 h optimistic, 125+ h pessimistic).
- The cost repeats per patch and per bound regime (a CPU-bound hub wants a different profile).

**Benchmark modes:**

| Game | Built-in benchmark | Source |
|---|---|---|
| MH Wilds | Separate free tool, Feb 2025 | [Guru3D](https://www.guru3d.com/story/monster-hunter-wilds-benchmark-released) |
| Wukong | Separate tool | [Steam 3132990](https://store.steampowered.com/app/3132990/) |
| Space Marine 2 | None at launch | [DSOG](https://dsogaming.com/pc-performance-analyses/warhammer-40k-space-marine-2-benchmarks-pc-performance-analysis) |
| Alan Wake 2 | None | [DSOG](https://dsogaming.com/?p=175483) |
| Stalker 2 | None | [DSOG](https://www.dsogaming.com/pc-performance-analyses/stalker-2-benchmarks-pc-performance-analysis/) |

- Both standalone tools are frozen pre-release builds. A profile tuned on a tool may not transfer to the patched game.
- Without a benchmark, reproduce scenes this way:
  - reload a save and move only the camera, at a fixed rate injected through uinput, in a static area;
  - use fixed "standing" viewpoints (DF style);
  - run at least 5 repeats.

**Failure modes:**
- Settings that interact non-additively, and the CPU/GPU-bound flip: GPU savings are worth 0 fps in Wilds hubs.
- The metric/human gap on temporal artifacts.
- Visibility-advantage knobs (fog off, foliage off) in multiplayer anti-cheat games. Exclude them.

**Tier:** S. Config files only.

**Verdict: SURVIVES WITH CHANGES.**
- Compare against the best Deck guide, not the nearest preset.
- Measure quality on a PC and cost on the Deck.
- Gate on the metric's noise floor, and use CVVDP + CGVQM together, sending disagreements to humans.
- Run cvar search on UE titles only.
- Use screening designs.
- Use at least 160 2AFC trials from at least 4 observers.

**Falsification (2 weeks), Wukong benchmark tool:**
1. **Day 1–2, noise floor.**
   - Deck at 15 W: 10 runs of stock Low.
   - PC: two max-settings reference captures at 1280×800 (200% scale, `-Deterministic`), scored against each other with CVVDP on the Deck display model.
   - **Kill** if Deck mean frame-time variation (coefficient of variation) is above 3%, or if reference-vs-reference CVVDP is below 9.5 JOD.
2. **Day 3–8:** screen about 100 cvars plus the menu settings.
3. **Day 9–10:** fill the budget to equal Deck ms (±2%) against both Medium and the SteamDeckHQ-style settings.
4. **Day 11–13:** blind 2AFC on the Deck. 4 observers × 40 trials = 160 trials of lossless clips.
5. **Pass:** ≥0.3 JOD **and** ≥58% preference (one-sided p<0.05) **and** Spearman ρ ≥ 0.6 between metric and human across ≥8 configurations.
6. **Kill:** <0.15 JOD, or the preference CI includes 50%, or <5% (1.1 ms) saved at equal JOD.
7. **Owner by hand:** tape-measure the viewing distance once, set the brightness slider and measure nits with a phone lux app, start the runner, sit the 2AFC sessions (about 20 min per person) and recruit 3 observers.

### E2. Motion blur at ~180° shutter on the OLED

- **Physics:** at 45 fps a 90°/s pan jumps about 98 px per frame. This holds whether the panel runs at 45 Hz or at 90 Hz with frames doubled.
- **Already done:** largely the default. Most target games ship motion blur on; per-game confirmation is [could not verify].
- **Cost:** 0.3–0.8 ms (est.), 1.4–3.6% of the budget.
- CVVDP will score it as error against a no-blur reference. **Only a preference test can judge it.**
- **Verdict: SURVIVES WITH CHANGES.** Treat it as one more price-list item, judged by preference test with the shutter amount as the variable.
- **Experiment:** 100+ trials at 30, 90 and 150°/s. Kill unless 180° is preferred at least 58% of the time at ≥90°/s.

### E3. HDR inverse tone mapping and a mid-contrast pass

- gamescope already has `--hdr-itm-enabled`, `--hdr-itm-sdr-nits`, `--hdr-itm-target-nits` ("only works for SDR input") and `--reshade-effect` (`main.cpp:148–150,155,216–219`) [checked].
- HDR-capable games already use native HDR on the Deck OLED. What's left is SDR games plus a local-contrast ReShade effect.
- **Risks:** fidelity metrics penalise it; static HUDs at high nits risk burn-in.
- **Verdict: SURVIVES WITH CHANGES, low priority.** Preference test only, with an APL/HUD-luminance cap. Kill at ≤50% preference.

---

## Cluster F: autotuning the driver, translation layer and compiler

### F1. SPIR-V recipes through `MESA_SPIRV_READ_PATH`

**Facts:**
- Added in Mesa 25.3, merged September 2025 ([Phoronix](https://www.phoronix.com/news/Mesa-SPIR-V-Shader-Replacement), MR 36472) [checked].
- Code: `src/compiler/spirv/spirv_to_nir.c:7914–7988`. It names files `0x<BLAKE3>.<stage>` and logs "Replacing shader…" (:7974).
- Docs: "usually necessary to disable the shader cache" ([docs.mesa3d.org/spirv](https://docs.mesa3d.org/spirv/index.html)) [checked].

**Why the cache must be off:**
- Replacement happens *inside* `spirv_to_nir`, after the pipeline-cache lookup.
- That lookup is keyed by the *original* SPIR-V hash (`radv_pipeline.c:1192–1211`).
- With a warm cache (Valve's), recipes **silently do nothing**.
- With a cold cache, the modified binary is stored under the original key. That is cache poisoning.
- Note that `MESA_SHADER_CACHE_DISABLE` disables the on-disk cache entirely (`envvars.rst:194`), so the stutter would come back on every launch.

**SteamOS 3.8 Mesa version:** 3.8.28 shipped a "new major" Mesa, version unnamed ([GamingOnLinux, 25 Sep 2026](https://www.gamingonlinux.com/2026/09/steamos-3-8-28-stable-released-with-big-improvements-for-steam-deck-steam-machine-and-more-hardware-support/)). The exact version is [could not verify]; a reader comment claims 26.1.2.

**Rescue:**
- Give each (game, recipe version) its own `MESA_SHADER_CACHE_DIR`.
- Pre-warm it on the Deck with `fossilize_replay` over the game's Steam `.foz` file, using the same environment variables.
- Confirm replacement with `MESA_SPIRV_LOG_LEVEL=info`.

**Hash churn:**
- The SPIR-V comes from vkd3d-proton/dxil-spirv.
- Proton stable bumped vkd3d-proton in 10.0-3, 10.0-4, 11.0-1 (7 Jul) and 11.0-2 (21 Aug) ([releases](https://github.com/ValveSoftware/Proton/releases)) [checked].
- So expect a re-dump, re-transform and re-warm about 4× a year per game (est.).
- Mitigation: key recipes on the DXIL hash too. Mesa already knows the DXIL hash vkd3d-proton embeds (`nir_spirv.h:157–160`).

**Budget:** 0–4% of GPU time, central about 1.5% (est.). NIR/ACO already fold and unroll. The real lever is specialising on constant uniforms, which needs a guard branch.

**Tier:** S only for bit-exact transforms verified on replay. A non-exact transform rewrites game GPU code, so it is Tier I in spirit.

**Verdict: SURVIVES WITH CHANGES** (rescue above).

### F2. Translation-layer knob sweep (`VKD3D_CONFIG`, dxvk.conf, `RADV_PERFTEST`)

**Facts:**
- About 73 `VKD3D_CONFIG` flags exist (`include/private/config_flag_decl.h`). Roughly a dozen affect performance: `no_upload_hvv`, `small_vram_rebar`, `no_staggered_submit`, `single_queue`, `memory_allocator_skip_*`, `recycle_command_pools`, `prefer_thin_uav_tiling`, `descriptor_heap`, `one_time_submit`. Several are correctness hazards.
- **The MH Wilds `no_upload_hvv` workaround is real and already on by default** (`device_workarounds.c:160–164`). The default UE workarounds (`SMALL_VRAM_REBAR`, `NO_STAGGERED_SUBMIT`) already apply to Wukong-class titles (`:811–820`). **The hand-found wins are in the status quo.**

**Wave32:**
- RADV defaults compute, pixel and geometry shaders to wave64 on GFX10.3. The source comment says "For pixel shaders, wave64 is recommended" (`radv_physical_device.c:2836–2860`).
- Shaders with workgroups of 32 or fewer threads already get wave32. Shaders using wide subgroup operations are forced to wave64 (`radv_shader.c:403–419`).
- I found no published per-game measurements of `cswave32` or `pswave32` [could not verify]. RadeonSI moved *toward* wave64 for cache-hit reasons ([Phoronix](https://www.phoronix.com/news/RadeonSI-More-Navi-Wave64)).

**Valve's cache:** **`RADV_PERFTEST` wave flags break it.** The wave sizes are part of `compiler_info.key` (`radv_device.c:1271–1274`). That key is hashed into `cache_hash` (`:903–916`), which feeds every pipeline hash (`radv_pipeline.c:1196`). Steam's background replay doesn't inherit launch options, so it can't pre-warm. Use the F1 pre-warm.

**Budget:** 0–3% central, with a heavy tail (est.). `WINE_CPU_TOPOLOGY`, `maxFrameLatency` and `latencySleep` overlap cluster C. Don't double-count them.

**Verdict: SURVIVES WITH CHANGES.** Run it as an overnight sweep, not a pillar. Exclude unsafe flags unless they pass a FLIP check and a 1-hour soak.

### F3. ACO per-pipeline knobs

- No hash-keyed per-pipeline knob exists. RADV's driconf has one wave option, which is for correctness (`00-radv-defaults.conf:126–127`).
- A custom Mesa changes the cache UUID, which is the build ID (`radv_physical_device.c:316–345`). That loses Valve's precompiled cache. It is also a side-loaded in-process driver, so Tier I.
- Is ACO already near-optimal? There's no direct proof. AMD dropping AMDVLK for RADV ([Phoronix](https://www.phoronix.com/news/AMDVLK-Discontinued)) suggests ACO is competitive.
- **Rescues tried:**
  - global `ACO_DEBUG`: these are debug switches and likely net-negative;
  - custom ICD: Tier I and loses the cache;
  - SPIR-V hints: loop control is expressible in SPIR-V, but register caps, scheduling and wave size are not;
  - upstreaming: viable, but slow.
- **Verdict: DEAD as a shippable product.** Two survivors: bench-only research to measure headroom, and loop-unroll hints folded into F1.

### F4. FP16 demotion

- vkd3d-proton already maps `min16float` to native 16-bit on RADV (`libs/vkd3d/device.c:10129–10133`). So the residual targets are shaders the developer kept at FP32.
- The change is not exact, so expect banding near black on the OLED.
- **Verdict: SURVIVES WITH CHANGES.** Make it an F1 transform for non-anti-cheat games only, judged by the E metric. Keep Round 1's kill rule: kill if most of the top-20 shaders show <50% ALU busy.

### Falsification for F (≤2 weeks, bench Deck)

1. **Day 1, facts on the Deck:**
   - `vulkaninfo` driverInfo: Mesa must be ≥25.3.
   - List `steamapps/shadercache/<appid>` to confirm a `.foz` exists.
   - Run with `MESA_SPIRV_READ_PATH` pointing at an empty folder and logging on. Count "not found" lines against the number of pipelines.
2. **Day 2, hash churn:** dump the top-20 hot-shader hashes under Proton 10.0-4 and 11.0-2. **Kill F1 shipping** if fewer than 50% survive the update.
3. **Day 3, cache:** first-10-minute count of frames over 50 ms with `cswave32`, against stock. Then pre-warm and repeat. **Pass** if the pre-warmed count is within 10% of stock.
4. **Day 4–10, sweep:** the Wilds and Wukong benchmarks. Stock, then each flag alone, then the three wave32 flags, then successive halving. 10 reruns of the winner against stock.
   - **Pass:** at least 3% better on mean GPU frame time or p99, with the 95% CI excluding 0, and FLIP no higher than stock-vs-stock.
   - **Kill:** all configurations below 2%.
5. **Day 11–12, headroom (bench-only, not shippable):** per-pipeline thread-trace profiling (RGP) of the top 20 under global options. **Kill F3/F4** if none moves at least 8%.
6. **Owner by hand:** install the runner, start the overnight sweeps, and switch Proton versions in Steam's settings for step 2.

---

## Claims dated after June 2026

| Claim | Status |
|---|---|
| CVVDP v0.5.7 (2 Aug 2026) | [checked: live README] |
| SteamOS 3.8 runs Linux 6.16 | [contradicted in part]: 3.8.10 (18 Jun 2026) was 6.16 ([Phoronix](https://phoronix.com/news/SteamOS-3.8.10-Stable)); 3.8.28 moved to 6.18.50 ([GOL](https://www.gamingonlinux.com/2026/09/steamos-3-8-28-stable-released-with-big-improvements-for-steam-deck-steam-machine-and-more-hardware-support/)) |
| SteamOS 3.8 Mesa version | [could not verify] |
| RADV `VK_EXT_descriptor_heap` on by default in 26.2 (5 Aug 2026) | [checked]: [Phoronix](https://phoronix.com/news/Mesa-26.2-Released) |
| vkd3d-proton's `descriptor_heap` | [checked]: per-game opt-in only (`device_workarounds.c:134,215,225`); 3.0.1 is "the last release before `VK_EXT_descriptor_heap` lands" (CHANGELOG) |
| Proton 11.0-1 and 11.0-2 bumped vkd3d-proton | [checked]: GitHub releases |

## Verdict table

| Idea | Verdict |
|---|---|
| E1 price list | SURVIVES WITH CHANGES |
| E2 OLED motion blur | SURVIVES WITH CHANGES (folds into E1, preference-judged) |
| E3 HDR inverse tone mapping + contrast | SURVIVES WITH CHANGES (low priority) |
| F1 SPIR-V recipes | SURVIVES WITH CHANGES |
| F2 translation-layer sweep | SURVIVES WITH CHANGES (overnight sweep) |
| F3 ACO per-pipeline | DEAD as shippable |
| F4 FP16 demotion | SURVIVES WITH CHANGES (F1 transform, non-anti-cheat only) |

## What would change my mind

- **E1:** reference-vs-reference CVVDP ≥9.7 JOD on the Deck model, plus ρ ≥0.8 between metric and human. That would make it worth more than I estimate.
- **E2:** a frame-rate-matched study showing blur preference collapses on OLED. That kills it.
- **E3:** any blind preference over 65% for Medium plus the pass against High. That would raise its priority.
- **F1:** at least 70% of hashes surviving a Proton bump, and at least 3% from uniform specialisation.
- **F2:** published per-game `cswave32` gains of 5% or more on RDNA2.
- **F3:** Mesa merging a per-pipeline-hash override in driconf. That would make it shippable.
- **F4:** at least 30% of hot ALU-bound shaders being FP32-only with no precision need.

**Key facts to keep:**
- The MH Wilds `no_upload_hvv` and default UE vkd3d-proton workarounds are already on by default.
- `RADV_PERFTEST` wave flags invalidate every pipeline cache key.
- `MESA_SPIRV_READ_PATH` is silently skipped when the shader cache is warm.
- CVVDP's correlation on rendering artifacts is PLCC 0.744 (CGVQM: 0.871).
- 30 2AFC trials only detect effects of about 1 JOD.
