## Cluster C red-team: frame-deadline CPU/GPU scheduling and power

### Headline
1. **Much of this cluster already ships in SteamOS, or is unreachable without fighting Steam.**
   - SteamOS has set `* hard nice -8` since at least the Feb 2024 build, so Wine priorities are already applied.
   - THP=always is the kernel default.
   - amd-pstate runs in active mode with EPP=balance_performance.
   - LAVD is an opt-in toggle, not the default.
   - CAPPED/UNCAPPED is a profile pair that Valve's own steamos-manager exposes. It is not undocumented.
2. **The budget claims don't survive the epp_boost author's own data.**
   - Civ VI: average fps was **unchanged**, even though the busy core's median clock rose from 2.43 to 3.5 GHz. p99 improved only 4.1%. Package power rose +1.0 W, and fps/W fell 10%.
   - vkmark, CPU-bound: +6.1% fps. vkmark, GPU-bound: +0.1%.
   - So "33 → 39 fps" (+18% average) is contradicted.
3. **The best measured lever is a mode switch, not a frame-phase governor.**
   - `amd_pstate=guided` with schedutil gave Civ VI a worst-1% frame time of 47 ms, against 63 ms with epp_boost and 70–73 ms on stock. p999 was 51 ms against 75–77 ms. Rendering power rose only +0.11 W, which was not statistically significant (LPC 2026 slides).
   - It is a single runtime sysfs write, so Tier S.
4. **A new finding nobody listed.**
   - SteamOS's `holo-cfs-debugfs-settings` writes `latency_ns`, `min_granularity_ns` and `wakeup_granularity_ns`. Those files don't exist on 6.16 (EEVDF).
   - So Valve's intended low-latency CFS tuning has been silently dead since kernel 6.6, and the base slice sits at 2.8 ms.

### 1. What SteamOS 3.8 already does
Sources: Valve's mirrors at github.com/Jovian-Experiments (steamos-customizations-jupiter, linux, PKGBUILDs-mirror) and github.com/evlaV (steamos-manager, jupiter-hw-support).

| Item | Finding |
|---|---|
| Kernel | 6.16.12-valveN, up to valve28 [checked: Valve tags; [Phoronix 2026-06-18](https://phoronix.com/news/SteamOS-3.8.10-Stable)]. 6.18.53-valve1 and 7.2.7-valve2 already exist in main/beta. |
| Default scheduler | EEVDF. LAVD is opt-in: steamos-manager v26.4.1 `power.rs:90-93` has `CpuScheduler{None,LAVD}`, and `power.rs:310-372` starts and stops `scx.service`. The scx-scheds PKGBUILD builds only scx_lavd and does not enable the unit [checked]. Whether a preset enables it on the device: could not verify. |
| amd-pstate | `CONFIG_X86_AMD_PSTATE_DEFAULT_MODE=3`, which is ACTIVE per `amd-pstate.h:116-120`. The grub cmdline (`etc/default/grub-steamos:16-27`) has no `amd_pstate=` override. SDTDP's README says Valve switched to amd-pstate-epp in 3.7.5 [checked]. |
| Default EPP | balance_performance (`amd-pstate.c:1510-1519`) [checked]. |
| Clock hints in active mode | Active mode is a `.setpolicy` driver with `adjust_perf=NULL` (`amd-pstate.c:1523,1693`). So **uclamp_min, schedutil and LAVD cpuperf hints cannot move clocks** [checked]. The outsider's "epp_boost + uclamp_min" arm is inert on stock SteamOS. |
| epp_boost | Not in any Valve kernel: amd-pstate.c at 6.16.12-valve28, 6.18.53-valve1 and 7.2.7-valve2 [checked]. It is an RFC ([LKML 2026-07-28](https://lkml.iu.edu/2607.3/07278.html)). Limonciello says it is "fighting with the hardware", and a governor redesign is proposed ([reply](https://lkml.iu.edu/2607.3/12462.html)). `dynamic_epp` exists in 6.18 and 7.2 but `CONFIG_X86_AMD_PSTATE_DYNAMIC_EPP` is unset. |
| RLIMIT_NICE | `misc/limits.d/15-proton-nice.conf:1`: `*   hard  nice    -8`. Present in tag jupiter-staging-20240212.1, absent in jupiter-rel-20230804.1. Wine raises its soft limit to the hard limit (`dlls/ntdll/unix/loader.c:2831-2832`) [checked]. |
| THP | `CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y` in the 6.5, 6.16, 6.18 and 7.2 configs. No userspace override found [checked]. |
| What Steam writes | `holo-priv-write:67-78` lets Steam write `power_dpm_force_performance_level`, `pp_od_clk_voltage` and `power*_cap`. steamos-manager writes `s 0 X / s 1 X / c` (`gpu.rs:371`), `power1_cap`/`power2_cap` (`power.rs:454-474`) and `pp_power_profile_mode` with values 8 or 9. Its comment (`gpu.rs:256`) reads: "Deck is designed to operate in one of the CAPPED or UNCAPPED power profiles". |
| Steam overwriting third-party settings | The mechanism is checked; the trigger is not. Every non-manual perf-level write resets per-core CCLK on all cores (`vangogh_ppt.c:1380-1381,1470-1484`). OD edits fail outside manual mode (`:2031`). The Steam client is closed source, so when it writes could not be verified. SDTDP ships "TDP Polling … for devices that change TDP in the background", which is circumstantial evidence. |
| Existing tools | SimpleDeckyTDP: per-game TDP, governor/EPP, SMT, GPU. PowerTools: per-core CPU frequency, SMT, GPU. CryoUtilities: THP=always (now default), compaction_proactiveness=0, khugepaged defrag=0, swappiness. MangoHud already has `throttling_status`. |

### 2. Source claims
- **[checked]** Wine `server/thread.c:265`: `if (nice_limit >= 0) return;` drops lowering as well as raising. The nice limit maps to [-8, +8] on SteamOS, so in a normal-priority process TIME_CRITICAL → nice -8, HIGHEST → -2 and LOWEST (DXVK compile threads) → +3.
- **[checked]** Proton `docs/THREAD_PRIORITY.md`.
- **[checked]** Thread names reach the kernel: `unix/thread.c:2013-2047` writes `/proc/<pid>/task/<tid>/comm`, called at `:2604` and from `ntdll/exception.c:239`. Names are truncated to 15 characters.
- **[checked]** EEVDF custom slice: `fair.c:5193-5202` clamps it to 0.1–100 ms, and it is unprivileged for the same user (`syscalls.c:458-512`). Two gotchas:
  - `sched_setattr` also overwrites nice, so the daemon must read and preserve it.
  - Under sched_ext the slice is BPF-owned, so custom slices and LAVD are mutually exclusive.
- **[checked]** SCHED_IDLE maps to `WEIGHT_IDLEPRIO` under scx too (`ext.c:3864`).
- **[checked]** Default slice: 0.7 ms × (1 + log2 8) = 2.8 ms (`fair.c:79,194-213`). Valve's `debug.c:510-518` exposes only `base_slice_ns`.
- **[checked]** `vangogh_ppt.c`:
  - Per-core CCLK exists, but the kernel keeps one shared min/max plus `cpu_core_id_select` (`:2045,2134`), and it needs manual mode.
  - FCLK forcing (`:1191-1207`) also needs manual mode (`amdgpu_smu.c:2522`).
  - PROFILE_PEAK pins GFX at 1300 MHz (`vangogh_ppt.h:37`), so it can't be used.
- **[checked]** `NtYieldExecution`: getrusage + sched_yield + getrusage (`unix/sync.c:2427`).
- **[contradicted]** "Valve acknowledged sibling sleep wipes L2" ([#864](https://github.com/ValveSoftware/SteamOS/issues/864)): the thread has no Valve-employee statement. It is an SMT-toggle request about a bug fixed around 3.5.
- **[checked]** Wine `MADV_NOHUGEPAGE` (`virtual.c:467`) applies only to kernel write-watch ranges, i.e. Unity/.NET GC heaps. None of the five target engines use those.

### 3. Budget redo
- **Clock vs memory latency.**
  - DRAM latency is about 150 ns, which is 390–525 core cycles.
  - I estimate 35–55% of a CPU-bound Deck frame is memory-stall time (est.). So even a sustained +27% clock buys at most +10–17% in a purely CPU-bound frame.
  - It also costs about +1 W (measured: LPC). At a binding 15 W that watt comes from the GPU: about −3% GPU clock, about −1% fps in GPU-bound frames (using SDHQ's 0.2–0.36 fps-per-clock elasticity).
- **The epp_boost +31.8% is cherry-picked in shape, not in the data.**
  - It is one single-thread CPU-bound game with short futex sleeps (LPC slides: +29–38%).
  - Other workloads: +6.1% (CPU-bound vkmark), +0.1% (GPU-bound vkmark), Factorio stalls 4/25 → 0/25.
- **Which targets are CPU-bound** (Deck fps measured; the CPU/GPU attribution is my estimate):
  - **SM2:** at forced 640×400 it still can't hold 30, and drops to 14 fps in hordes ([SDHQ](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/)). Likely CPU or fixed-cost bound.
  - **Stalker 2:** about 15 fps native, about 20–23 with FSR Ultra Performance ([GOL](https://www.gamingonlinux.com/2024/11/stalker-2-heart-of-chornobyl-review-works-on-linux-desktop-with-proton-but-poorly-on-steam-deck/page=3)). Mixed.
  - **MH Wilds 1.040:** "more related to the GPU than the CPU" ([SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-1040-performance/)).
  - **Wukong, AW2:** GPU-bound (est.; no Deck CPU data found).
- **My numbers for the whole cluster at 15 W** (pessimistic / central / optimistic):
  - average fps in CPU-bound scenes: 0 / +3% / +8%;
  - average fps in GPU-bound scenes: −1.5% / 0 / +1%;
  - p99 frame time in SM2/Stalker hubs: 0 / −5% / −25%;
  - 1% lows: 0 / +8% / +30%.
- **Double-counting.**
  - Undervolt, watt arbitrage, GPU caps and CAPPED all draw on one pool, "GPU power headroom". That pool is zero unless the power-limit throttle bits fire. EPP/guided boosts spend that same pool. So these levers net against each other, not add.
  - Clusters A and B (GPU savings) make scenes more CPU-bound, which raises C's value. That is an interaction, not double-counting.

### 4. Per idea
1. **Wine RLIMIT_NICE: DEAD.** It already ships.
   - Rescue tried: raise the limit to −20. Under EEVDF, nice changes weight, not slice; nice −8 is already about 6× the weight of nice 0, and compile threads already get +3. Expected gain about 0.
   - Keep one verification: `grep -i nice /proc/<game pid>/limits` should show 28.
2. **Critical-path QoS (custom slice + SCHED_IDLE): SURVIVES WITH CHANGES.**
   - (a) Test the global `base_slice_ns` 2.8 → 0.7 ms first. This restores Valve's lost intent with one root write.
   - (b) Use per-thread 0.3 ms slices only under EEVDF, preserving nice.
   - (c) Put only decompression and IO workers on SCHED_IDLE. Starving shader compile threads risks more stutter.
   - Risks: more context switches for UE5 task graphs, and game patches renaming threads.
   - Anti-cheat: Wine keeps its own copy of thread priority and affinity, so Linux-side changes are invisible to the game (est.). Tier S holds.
3. **LAVD SMT shielding: SURVIVES WITH CHANGES.**
   - Prototype with `sched_setaffinity` and a cpuset (critical thread alone on its core) before forking Valve's packaged LAVD.
   - LPC data: EPP must be written to both siblings; one sibling alone is bistable.
   - Risk: UE5 loses 1 of 8 logical CPUs. LWN reports LAVD is weak on UE games.
4. **EPP pre-boost / frame-phase governor: DEAD as a per-frame predictor.**
   - Rescues tried:
     - per-frame min_perf: upstream measured a p999 regression of 13–21%;
     - per-frame EPP: it is only a hint into a roughly 1 s firmware estimator, so a 0.5 ms lead is meaningless (est.).
   - **Rescued as a different idea: "static gaming CPU mode"**, either guided mode or EPP=performance on both siblings of the critical cores. **SURVIVES WITH CHANGES.**
   - Also note: Mesa 26.3 anti-lag adds deliberate CPU sleeps, which likely worsen EPP droop (est.). That makes the static mode more valuable once anti-lag ships.
5. **C-state guard: SURVIVES WITH CHANGES, as one A/B arm only.**
   - Its rationale is contradicted (see section 2). CC6 also needs both siblings idle.
   - Expected 0–2% on p99, with a power cost.
6. **Watt arbitrage with per-core CCLK: DEAD for fps.**
   - In GPU-bound scenes the CPU is already at 2–3 W ([C&C](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)). Freeing about 0.5 W gives roughly +0.3–0.7% fps, below noise.
   - It needs manual mode, which Steam's perf-level writes reset.
   - Rescues tried: mixed scenes (≤1% est.); battery saving (not the goal); LAVD core compaction (already exists).
7. **CAPPED profile: mostly ALREADY DONE**, since Valve manages it. **SURVIVES** only as a one-hour check: read which profile Steam sets, then A/B the other.
8. **fclk/mclk pinning: SURVIVES WITH CHANGES, measure first.**
   - It needs manual mode, and PROFILE_PEAK can't be used (GFX pinned at 1300 MHz).
   - Only act if logging shows FCLK below max in more than 5% of GPU-bound frames.
9. **Undervolt bisection: SURVIVES WITH CHANGES.**
   - DeckForge only guides and validates; the user sets the BIOS offsets.
   - Include a cold-boot test.
   - The fps value at 15 W depends on the throttle bits. Measured elsewhere: OLED at −20/−50/−50 mV matched stock 10 W performance at 9 W.
   - Risk: silent corruption.
10. **Throttle-bit logging: SURVIVES.** It is the gate for items 6–9. MangoHud already displays it; `throttle_status` is at `vangogh_ppt.c:1697`.
11. **THP / 16K pages: DEAD as proposed**, because 2 MB THP is already the default. The residual 16K multi-size THP (`hugepages-16kB`) arm **SURVIVES WITH CHANGES**, as a one-day check expecting 0–2%.

### 5. Post-June-2026 claims
- SteamOS 3.8 on 6.16 with LAVD: [checked]. LAVD is opt-in.
- Mesa 26.3 `vk_frame_pacer` / `VK_AMD_anti_lag`: [checked] ([Phoronix 2026-10-08](https://phoronix.com/news/Mesa-26.3-RADV-VK_AMD_anti_lag)).
  - Stable release is due in November, so it is not on 3.8.
  - It lives in-process, so a Tier S daemon can't read its state.
  - Whether it is on by default, and whether DXVK uses it: could not verify.
- LPC 2026 ([talk](https://lpc.events/event/20/contributions/2403/), 2026-10-05): [checked]. Numbers are as quoted above.
  - "Wine/Proton thread hints" is an open question, backed by a 7950X UCLAMP_MIN prototype (−41% work time), not a feature.
  - Its measurements were taken on the charger with RAPL, not at a binding 15 W cap. That is the gap DeckForge must test.

### 6. Falsification experiment (one shared bench, 2 weeks, bench Deck OLED, driven by the bench runner)
- **Day 1, read-only gate (G0).**
  - Check the status quo: nice limit 28, `amd_pstate/status`, EPP, THP, `scx.service`, `base_slice_ns`, AnonHugePages.
  - Log `gpu_metrics` at 20 Hz: `throttle_status`, per-core clocks, gfx/core/soc power. Also log `pp_dpm_fclk`.
  - Run 5 scenes: SM2 hub and a horde, a Stalker 2 hub, the Wilds benchmark, the Wukong benchmark. Civ VI is the positive control.
  - **Kill items 6, 7 and 9 (for fps) and the GPU-cap arm** if the SPPT/FPPT/STAPM bits are set in less than 20% of GPU-bound samples.
  - **Kill item 8** if FCLK sits at max in more than 95% of samples.
- **Days 2–10: arms.** Each arm gets 10 interleaved ABAB runs at TDP 15 W, room temperature 20–25 °C, with the same frame-time logger in every arm. Before any arm, `perf sched` must show critical-thread runnable-wait p99 of at least 0.5 ms; otherwise kill arms 3 and 4.
  1. stock;
  2. guided mode;
  3. EPP=performance on both siblings of the cores hosting the critical threads;
  4. `base_slice_ns=700000`;
  5. arm 4 plus 0.3 ms custom slices plus SCHED_IDLE on decompression threads;
  6. SMT-shield prototype;
  7. deepest C-state disabled on critical cores;
  8. the CAPPED/UNCAPPED A/B (only if G0 passes);
  9. 16K mTHP.
- **Pass:**
  - p99 frame time at least 8% better (95% CI excludes 0) in at least 2 target scenes;
  - average fps no worse than −1% in GPU-bound scenes;
  - energy per frame up by no more than 5%.
- **Kill:**
  - p99 improves less than 3% in every target scene; or
  - average fps loses more than 2% in any GPU-bound scene.
- **Validity check:** Civ VI under guided mode must reproduce a worst-1% improvement of at least 20%. If it doesn't, the bench is broken, not the idea.
- **Undervolt (days 11–14).**
  - The owner sets the BIOS offsets: GPU/CPU {0, −20, −30, −40} mV; SoC 0 or −10 only.
  - Validation: 2 × 20 minutes of checksum-verified CPU and GPU kernels, cold (after 30 minutes powered off) and warm.
  - **Pass:** zero errors at the chosen offset plus a 10 mV margin, and either +2% fps at 15 W or 1 W saved at equal fps.
  - **Kill:** any error, or less than 1% fps gain and less than 0.5 W saved.
- **What the owner does by hand.**
  - Quick Access Menu: TDP 15 W, frame limit off, Manual GPU Clock off, per-game profile off.
  - Launch each scene when prompted, and don't touch the controls during fixed-camera runs.
  - Set the BIOS offsets (Vol+ and Power → Setup Utility).
  - Keep the room temperature constant.

### Verdict table
| Idea | Verdict |
|---|---|
| Wine RLIMIT_NICE | DEAD (already shipped) |
| sched_setattr slices + SCHED_IDLE | SURVIVES WITH CHANGES |
| LAVD SMT shielding | SURVIVES WITH CHANGES |
| EPP pre-boost / frame-phase governor | DEAD as per-frame; rescued as a static guided/EPP mode, which SURVIVES WITH CHANGES |
| C-state guard | SURVIVES WITH CHANGES (one arm only) |
| Watt arbitrage with per-core CCLK | DEAD (for fps) |
| CAPPED profile | Mostly done by Valve; one-hour check survives |
| fclk/mclk pinning | SURVIVES WITH CHANGES (gated on logs) |
| Undervolt bisection | SURVIVES WITH CHANGES |
| Throttle-bit logging | SURVIVES |
| THP / 16K pages | DEAD for 2 MB; 16K arm SURVIVES WITH CHANGES |

### What would change my mind
- **RLIMIT_NICE:** the game's `/proc/<pid>/limits` shows a nice limit of 0, i.e. PAM limits don't reach gamescope-session.
- **Slices / SCHED_IDLE:** `perf sched` shows critical-thread wait p99 of at least 1 ms caused by same-CPU competitors.
- **SMT shielding:** a busy sibling is present for more than 30% of the critical thread's runtime, and SMT-off improves p99 by at least 8%.
- **Frame-phase governor:** a per-frame controller beats the static guided mode by at least 5% p99 in the A/B.
- **C-state guard:** CC6 residency on critical cores during frames exceeds 20%.
- **Watt arbitrage:** power-limit bits are set in at least 30% of GPU-bound frames while the CPU draws more than 4 W.
- **CAPPED:** the non-default profile gives at least 3% average fps at equal power.
- **fclk:** FCLK falls below max in more than 5% of GPU-bound frames.
- **Undervolt:** a checksum error appears at the chosen margin. That would kill it.
- **Throttle logging:** reading gpu_metrics at 20 Hz itself costs more than 1% fps.
- **THP:** game AnonHugePages is below 30% of its resident memory.

### Key facts to keep
- SteamOS ships `* hard nice -8` (since ≤ Feb 2024), so Wine priorities are applied.
- amd-pstate is in active mode with EPP balance_performance. uclamp has no effect in that mode.
- THP=always is the kernel default.
- LAVD is an opt-in steamos-manager toggle.
- Valve's CFS debugfs tunings are no-ops on EEVDF, leaving the base slice at 2.8 ms.
- epp_boost is RFC-only and was not shipped. At LPC 2026, guided mode beat it on Civ VI tails.
- Mirrors that work: Jovian-Experiments (steamos-customizations-jupiter, linux, PKGBUILDs-mirror) and evlaV (steamos-manager, jupiter-hw-support), reachable via raw.githubusercontent.com and git clone.

Local copies of the source I checked: `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/dlc/`, `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/scj.QWeH/` (scj, sm, jhw, pkg).
