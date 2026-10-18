# Round 2 input: the Round 1 ideas, clustered and deduplicated (2026-10-18)

Seven specialists worked independently from the shared brief
(`/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/brief.md`).

Full reports, with their citations, are in
`/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/round1/`:

| File | Specialist |
|---|---|
| `1_console_port.md` | console-port graphics engineer |
| `2_neural.md` | neural rendering |
| `3_perception.md` | perception / display science |
| `4_systems.md` | kernel / driver / compiler |
| `5_power.md` | hardware / power / thermal |
| `6_precompute.md` | offline precomputation |
| `7_outsider.md` | adjacent fields |

**All millisecond and fps figures below are Round 1 estimates, not measurements, unless a report cites a measurement.**

---

## The overall problem in numbers (from 1_console_port.md, est.)

- The PS5 has about 6.3× the Deck's compute and about 5.6× its memory bandwidth.
- At 960×600 internal resolution, a PS5-60-fps UE5 frame comes out at roughly **48–55 ms on the Deck at a High-like look (~19 fps)**.
- About **54–66% of that Deck frame is work that does not shrink with resolution**: lighting caches, culling, shadow geometry and similar.
- So lowering resolution alone cannot close the gap.
- The console-port specialist's honest ceiling for pass-level tricks: about 28–33 fps at a High-like look. Not 45.
- A separate observation from 3_perception.md and 6_precompute.md: at handheld distance the Deck is about **42–56 pixels per degree**.
  - That is at or slightly below what the eye resolves at the screen centre (~60 ppd).
  - So "the small screen hides it" is weaker than people assume.
  - The perceptual slack is in **motion, darkness, mid-scale contrast and latency**.

---

## Clusters

### A. Driver-forced variable-rate shading, motion/content-aware (Tier S)

**Sources:** 1_console_port #2, 7_outsider #2, 3_perception #2 and #3. Three specialists reached this independently.

**Mechanism:**
- RADV's `RADV_FORCE_VRS` / `RADV_FORCE_VRS_CONFIG_FILE` forces 2x2, 2x1 or 1x2 coarse shading on pipelines that don't use VRS themselves.
- The Mesa docs say the config-file variant "only affects GFX10.3 APUs" (Van Gogh) and is re-read at runtime.
- A daemon sets the rate from motion:
  - 2x1 during yaw pans, 1x2 during pitch pans;
  - 2x2 on flicks and for ~130 ms after scene cuts;
  - 1x1 when still.
- Later versions:
  - a per-pipeline-class policy: particles and blur at 2x2, UI at 1x1;
  - a per-tile rate image driven by luminance, contrast and predicted gaze;
  - both would need a Mesa patch or a Vulkan layer.

**Claimed gain:** 1.8–5 ms per frame during pans (est.).
- Desktop RDNA2 at 4K showed +8% with blanket 2x2 (Phoronix).
- "30%+" in some games and nothing in others.

**Cheapest test:** one evening, a launch option, 5 games, GPU ms plus perceptual score.

### B. Temporal amortization of fixed-cost passes: the port team's "update fraction" (mostly Tier I; UE5 cvars Tier S)

**Sources:** 1_console_port #1 (Pass Interleaver) and #3 (far shadow cascades, exact memo); 2_neural #5 (learned pass skipping) and #2 (async history refinement); 6_precompute #2 (Tier I per-pass schedule).

**Mechanism:**
- A Vulkan layer rebuilds the pass graph and identifies temporally accumulated compute passes: GI, volumetrics, AO, SSR, clouds.
- It runs those every 2nd or 3rd frame, interleaved so frame time stays flat.
- It skips byte-identical passes exactly (exact memo).
- It refreshes far shadow cascades every 2–4 frames.
- For UE5 the same knob exists as Engine.ini cvars (`r.LumenScene.Radiosity.UpdateFactor` and similar). Those are Tier S and should be tried first.

**Claimed gain:** 5–7 ms at half rate on the fixed-cost passes, plus about 2 ms from shadows (est.).

**Foundation it needs: the "Replay Lab".**
- Capture gameplay with GFXReconstruct and replay it deterministically on a Deck to measure per-pass ms and quality.
- Captures contain game assets, so they stay local.
- Capture itself is Tier I, so it can't be used on anti-cheat games.

### C. Frame-deadline-aware CPU/GPU scheduling and power (Tier S)

**Sources:** 4_systems #1 and #2; 5_power #1–#4; 7_outsider #1. Three specialists overlap here.

**Mechanism pieces:**
1. **Wine thread priorities.** Wine drops Windows thread priorities unless RLIMIT_NICE allows them (Proton `server/thread.c:265`). Also drops DXVK's LOWEST priority for compile threads. Fix: `LimitNICE` for the game scope.
2. **Critical-path QoS.**
   - Identify critical threads by name; Proton copies SetThreadDescription into `/proc/.../comm`.
   - Give them short custom slices via `sched_setattr`.
   - Put compile and decompression workers on SCHED_IDLE.
   - A LAVD sched_ext extension adds SMT-sibling shielding.
3. **Frame-phase power governor.**
   - EPP pre-boost of the critical core before its predicted wake. The SMU takes about 1 s to ramp.
   - C-state guard on critical cores.
   - In CPU-bound phases, cap the GPU clock and pin fabric/memory clock high. The reverse in GPU-bound phases.
   - Try the undocumented CAPPED profile.
4. **Watt arbitrage.** Per-core CPU clock caps on non-critical cores (`pp_od_clk_voltage` "p core N"), so freed watts go to the GPU.
5. **Supporting items:**
   - user-set undervolt from the official BIOS menu, with an error-checking bisection;
   - throttle-bit logging to see which limit actually binds;
   - THP / 16K pages for game heaps (4_systems #4).

**Claimed gains (est.):**
- p99 frame time −10–25%, average −0–8%.
- In CPU-bound hubs, 33 → 39 fps.
- GPU-bound scenes: +2.5–7%.

**Prior art:** epp_boost reported +31.8% 1% lows on the Deck in Civ VI.

### D. Per-game small neural reconstruction (Tier I) and a compositor restoration filter (Tier S)

**Sources:** 2_neural #1 (DeckSR) and #3 (RAISR/HKLUT in gamescope); 6_precompute #3; 7_outsider #5. Several specialists overlap.

**D1 (Tier I):**
- An NSS-style parameter-prediction network, about 1.5 GMAC per frame, INT8/INT4 dot products, with per-game adapters. Fed through OptiScaler.
- Claim: 512×320 internal resolution at FSR2-at-640×400 quality, for about 2–2.4 ms.
- Net gain about 4.5–6 ms (est.).

**D2 (Tier S):**
- The game keeps its own TAAU/FSR2. gamescope applies a per-game learned filter (RAISR buckets or a lookup-table CNN) trained on Low/Medium vs High pairs.
- Costs 0.3–1.6 ms.
- Claim: +0.2–0.25 JOD.

### E. Perceptual price list: per-game settings and cvar search scored at the Deck's own viewing geometry (Tier S)

**Sources:** 6_precompute #2; 7_outsider #3; plus 3_perception #4 (motion blur ~180° shutter on OLED at 45 fps) and #5 (HDR highlight expansion and mid-scale contrast).

**Mechanism:**
- For every setting and cvar, measure Δms on the Deck.
- Measure ΔJOD with ColorVideoVDP using a custom Deck display model: 7.4", 1280×800, the measured viewing distance, OLED nits.
- Fill the frame budget by equal marginal value, using Bayesian optimization for interactions.
- Ship the result as an ini/profile.

**Claimed gain:** 0.5 JOD at equal ms, or 2–6 ms at equal JOD (est.).

**Caveat raised in Round 1:** ColorVideoVDP has no foveation or smooth-pursuit model, and FLIP defaults to 67 ppd, not 42.

### F. Offline autotuning of the driver / translation layer / shader compiler per game (Tier S)

**Sources:** 6_precompute #1 (shader recipes via Mesa 25.3+ `MESA_SPIRV_READ_PATH` by BLAKE3 hash); 7_outsider #4; 4_systems #3 (VKD3D_CONFIG, dxvk.conf, `RADV_PERFTEST` wave32, `WINE_CPU_TOPOLOGY` search) and #6 (ACO per-pipeline knobs); 1_console_port #4 (per-shader FP16 demotion).

**Mechanism:**
- Search on a Deck farm over existing knobs.
- Ship only {hash → knobs} or env-var strings. No shaders, no game code.

**Claimed gains (est.):** 0–10% from the translation-layer knobs; 1–2.3 ms from compiler knobs on the top pipelines.

**Known risk:** shader replacement needs `MESA_SHADER_CACHE_DISABLE`, which would lose Valve's precompiled cache and bring back stutter.

### G. Stick/gyro-latched camera reprojection in gamescope (Tier S, but presented fps only)

**Sources:** 2_neural #4; 3_perception #1. Two specialists overlap.

**Mechanism:**
- At each 90 Hz vblank, warp the newest game frame to the camera angle implied by the latest stick or gyro input.
- Use a per-game stick→camera curve fitted offline.
- Use low-res optical flow, which captures orbit-camera parallax, or a pure rotation warp in first-person games.

**Claimed:**
- Camera-turn latency drops from 50–90 ms to 10–20 ms.
- Costs about 0.9 ms of GPU.
- Removes judder.

**Note:** under DeckForge's rules this is like frame generation. It does not count toward native fps, but it does count toward "plays well" (latency and smoothness).

### H. Harvested GI ("photogrammetry of light") (Tier I, UE5)

**Source:** 6_precompute #4.

**Mechanism:**
- Turn Lumen off with `r.DynamicGlobalIlluminationMethod=0` (Tier S).
- Replace it with irradiance probes harvested from the game's own max-settings output on contributors' PCs, with a time-of-day basis.
- One compute pass on the Deck applies them.

**Claimed:** saves 4.5–8 ms. Needs 0.1–0.6 GB of data per game.

**Risks:** dynamic lights, losing reflections, per-version data. Legal question: does shipping measured lighting count as a derivative of assets?

### I. Smaller or long-shot items

- Shadow PVS (6_precompute #5).
- Bandwidth diet: format demotion and half-res particles (1_console_port #5, Tier I).
- Wine syscall tax and a Deck-native `-march=znver2` + PGO Proton build (4_systems #5).
- Forced-air cooling accessory (5_power #5).
- Tethered higher TDP via BIOS mod (5_power #6, not shippable).
- USB NPU (5_power #7, mostly negative).
- CPU as a neural coprocessor (2_neural #6, negative).
- Publisher/upstream pressure via telemetry, evidence packets and funding (7_outsider #6).

---

## Claims dated after June 2026 that need checking before anything rests on them

- Mesa 26.3 `vk_frame_pacer` / VK_AMD_anti_lag in RADV (Phoronix, Oct 2026).
- Valve showing developers Deck frame-rate telemetry (Oct 2026).
- AMD FSR 4 for RDNA2 including the Deck in early 2027.
- GE-Proton 11-3 OptiScaler integration.
- `VK_EXT_descriptor_heap` on by default in RADV 26.2.
- Marek Olšák's VRS fixes in Mesa 26.2.
- SteamOS 3.8 on Linux 6.16 with LAVD support.
- David Vernet's epp_boost patch status: merged or not, and shipped in SteamOS or not.
- LPC 2026 talk content.
