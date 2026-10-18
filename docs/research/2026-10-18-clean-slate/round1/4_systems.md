## DeckForge, systems/driver/compiler angle: six ideas to make the CPU side cheaper from below

**Sources I read** (pinned): Linux v6.16, which Phoronix reports as the SteamOS 3.8 default; Proton 11 Wine (`ValveSoftware/wine proton_11.0`); DXVK `52fe923c` (2026‑09‑25); vkd3d‑proton `0bb64c56` (2026‑10‑14); `scx_lavd` (sched-ext/scx main); the kernel's `vangogh_ppt.c` (the Deck's SMU power-management driver).

**Measured facts everything below rests on**
- **Clock ramp:** the Deck's CPU goes from 1.4 to 1.7 GHz in 0.27 ms, then takes about 1 s to reach full clock ([Chips and Cheese](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)).
- **Power split:** when GPU-bound, the GPU draws more than 10 W while the CPU is "squished below base clock" at 2–3 W (same source).
- **Memory:** DRAM latency is about 150 ns; the CPU side gets only about 25 GB/s (same source).
- **Scheduler slice:** EEVDF (the default Linux scheduler) gives each task 0.7 ms × (1+log2 8) = **2.8 ms** on 8 CPUs (`kernel/sched/fair.c:79,196–208`). `RUN_TO_PARITY` blocks wake-up preemption until the running task uses up that slice (`features.h`).

---

### 1. Frame-critical-path QoS (rank 1)
**Pitch:** tell the kernel which 3–5 threads *are* the frame, and keep everything else away from them.

**Mechanism**
- **(a) Restore priorities Wine throws away.** Wine applies Windows thread priorities only when RLIMIT_NICE (the per-process limit on raising thread priority) is above 20. Otherwise `apply_thread_priority` returns at once (`server/thread.c:265`, `if (nice_limit >= 0) return;`). Proton's own `docs/THREAD_PRIORITY.md` says this needs system configuration.
  - The early return also drops *lowering*. DXVK asks for `THREAD_PRIORITY_LOWEST` for its shader compilers (`dxvk_pipemanager.cpp:121` → `util/thread.cpp:48`), and that request is discarded too.
  - LAVD only sees nice values (`lat_cri.bpf.c:111`), so it can't tell compile threads from game threads.
  - Fix: `LimitNICE=30` for the game's scope.
- **(b) Find critical threads by name.** Proton copies both `SetThreadDescription` and the 0x406D1388 naming exception into the Linux thread name (`/proc/…/comm`) (`unix/thread.c:2013–2043`, `ntdll/exception.c:229`).
  - That makes these visible: GameThread, RenderThread, RHIThread, `dxvk-cs`, `dxvk-submit`, `vkd3d_queue`, `vkd3d_fence`.
  - A GPU-completion wake reaches the game in two hops: `vkd3d_fence` thread → NT event → game.
- **(c) Policy, in two steps.**
  - No BPF needed: a same-user daemon sets a 0.2–0.3 ms custom slice on the critical threads via `sched_setattr.sched_runtime`. This is unprivileged (`fair.c:5188`, clamped 0.1–100 ms), and with `PREEMPT_SHORT` it lets them preempt immediately. It also puts `dxvk-shader-*`, `vkd3d-disk$` and decompression workers on `SCHED_IDLE`.
  - Then a `sched_ext` extension of LAVD:
    - SMT-sibling shielding while a critical thread runs;
    - demote yield-spinners and keep them off critical siblings. Each `NtYieldExecution` costs getrusage + sched_yield + getrusage (`unix/sync.c:2427`).

**Why it could beat the wall:** Linux sees 30–40 equal threads. The engines' priority hints exist but are discarded.

**Budget math**
- One wake behind a compile thread can cost up to 2.8 ms, which is 11% of a 25 ms frame. That is exactly what a 1%-low spike is.
- SMT (est.): a busy sibling runs the main thread at about 0.62× speed. If that happens for 40% of its runtime, shielding cuts its time by about 20% (1.245T → T), at the cost of 1 of 8 logical CPUs.
- Expected: p99 frame time −10–25%, average −0–8% (est.). Power cost: about 0.

**Prior art**
- [LAVD at LPC 2025](https://lwn.net/Articles/1051430/): Min lists "profile-guided, per-engine" scheduling as unexplored.
- [epp_boost](https://www.phoronix.com/news/AMD-P-State-Better-1p-Lows): +31.8% 1% lows on the Deck from a related wake/frequency fix.
- Android top-app cpusets + uclamp; consoles reserving cores for the game.

**Tier:** S. Applies to all games, including anti-cheat ones.

**Cheapest falsification:**
- Run `perf sched record`, 5 minutes each, in the MH Wilds benchmark, the Wukong benchmark and the SM2 hub.
- Per frame, measure the critical thread's runnable-wait time and the % of its runtime with a busy sibling.
- Kill if p99 wait is under 0.5 ms and the busy-sibling share is under 20%.
- Otherwise run a 20-run A/B on p99 frame time using gamescope timestamps. Don't use MangoHud batch logging; LWN reports it causes stutter.

**Biggest risk:** UE5 task-graph frames use all 8 threads, so shielding costs throughput. LWN also notes LAVD is reportedly weak on UE games.

### 2. Frame-phase power management (rank 2)
**Pitch:** the SMU reacts in about 1 s, but frames last 25 ms. Predict the frame instead of reacting to it.

**Mechanism:** a daemon reads present timestamps from gamescope, plus `gpu_metrics`: per-core clocks and power, and the CPU vs GFX power split (`vangogh_ppt.c`, gpu_metrics fill). It then:
- **Pre-boosts:** sets EPP=0 on the critical core about 0.5 ms before its predicted wake. The epp_boost author found that raising `min_perf` instead *regressed* frame-time tails on the Deck.
- **Guards C-states:** sets per-CPU `pm_qos_resume_latency_us` on critical cores during the frame, so they skip deep sleep (CC6, which loses the 512 KB L2) between bursts. Valve acknowledged that an idle SMT sibling's sleep could wipe the running thread's cache ([SteamOS #864](https://github.com/ValveSoftware/SteamOS/issues/864)).
- **In CPU-bound phases:**
  - lowers the GPU clock ceiling (`pp_od_clk_voltage`) to the minimum that still meets the GPU deadline, turning GPU idle time into CPU watts;
  - raises the fabric-clock floor (`pp_dpm_fclk`, `SMU_FCLK` case in `vangogh_force_clk_levels`) to cut DRAM latency;
  - the SMU also accepts a per-core CPU clock floor (`SetSoftMinCclk`).
- **In GPU-bound phases:** the reverse.

**Why it could beat the wall:** because voltage rises with frequency, running the GPU at a steady just-in-time clock costs less than racing to idle. CPU-bound hubs leave the GPU with slack.

**Budget math**
- Clock (est.): a 30 ms CPU-bound frame with the critical core averaging 2.6 GHz, raised to 3.3 GHz, with 65% of its time clock-sensitive: 0.35 + 0.65 × (2.6/3.3) = 0.86 → 25.8 ms, i.e. 33 → 39 fps.
- Power (est.): +1.5–2 W to the CPU, funded by dropping GFX from 1.6 to 1.2 GHz (about −2 to −3 W).
- Cold-wake refill (est.): 8192 L2 lines × 15–150 ns ÷ memory parallelism of 6 ≈ 20–200 µs per wake. Ten wakes per frame ≈ 0.2–2 ms.

**Prior art**
- epp_boost on the Deck (+31.8% 1% lows, Civilization VI).
- [Pathania, DAC'14](https://www.comp.nus.edu.sg/~tulika/DAC14.pdf): coordinated CPU+GPU frequency control for games, up to 26% less power than Linux at the same fps.
- [Android ADPF](https://developer.android.com/stories/games/unisoc-adpf): LineageW +28% fps at −3.7% power on medium settings.
- The Van Gogh SMU already has CAPPED/UNCAPPED workload profiles (`vangogh_workload_map`).

**Tier:** S. All games.

**Cheapest falsification:** test fixed settings first. In a CPU-heavy segment of the MH Wilds benchmark, compare default against {GFX cap 1.1 GHz + EPP=0 + FCLK at max + C1-only on critical cores}. Measure frame-time p50/p99 and watts from `gpu_metrics`. Kill if p50 improves less than 5% at equal APU power.

**Biggest risk:** the SMU firmware may override these limits.

### 3. Offline-autotuned translation layer per game (rank 3)
**Pitch:** the translation layers already ship dozens of per-game performance switches. Let a robot search combinations and ship the winning string as data.

**Mechanism**
- A Deck farm replays benchmark segments and runs Bayesian / successive-halving search over about 20 knobs:
  - `VKD3D_CONFIG` (≈70 flags), e.g. `no_upload_hvv`, `force_host_cached`, `no_staggered_submit`, `descriptor_heap`;
  - `dxvk.conf`: `cachedDynamicResources`, `numCompilerThreads`, `maxFrameLatency`, `latencySleep`, `relaxedBarriers`;
  - `RADV_PERFTEST=cswave32/pswave32/gewave32`;
  - `WINE_CPU_TOPOLOGY` (sets the size of the engine's thread pool).
- Objective: p99 frame time under an input-latency limit, with a FLIP gate on anything that changes output.

**Why it could beat the wall:** shared memory creates hidden costs. CPU reads and partial writes to write-combined memory are uncached. vkd3d-proton's own developers turned host-visible-VRAM uploads off for MH Wilds "since it's very CPU intensive" (`device_workarounds.c:160–164`). That win was found by hand; nobody searches combinations per game on the Deck.

**Budget math:** about 150 runs × 90 s ≈ 4 h per scene per Deck (est.). Expected gain 0–10% (est.), with a heavy tail.

**Prior art:** the per-exe tables in DXVK and vkd3d-proton, Mesa driconf, and NVIDIA/AMD per-game profiles.

**Tier:** S (environment variables only). All games.

**Cheapest falsification:** one game, two weeks. Kill if the best configuration beats default p99 by less than 3% (95% CI, 10 reruns).

**Biggest risk:** overfitting to the benchmark segment.

### 4. TLB reach: huge (and 16K) pages for game heaps (rank 4)
**Mechanism**
- Set THP=always with defrag=defer for the game, or use 16 KB multi-size THP (`hugepages-16kB`), so Zen 2's page-entry coalescing actually fires. Measured, Zen 2's L1 data TLB behaves like 192 entries ≈ 800 KB ([7-cpu](https://7-cpu.com/cpu/Zen2.html)).
- Wine never requests huge pages for heaps (no `MADV_HUGEPAGE`). It also *forces* huge pages off on write-watch regions (`virtual.c:466–467`), so Unity/.NET garbage-collected heaps never get them.

**Why it could beat the wall:** the L2 data TLB covers 2048 × 4 KB = 8 MB with normal pages versus 4 GB with 2 MB pages, and a TLB miss that goes to memory costs about 150 ns.

**Budget math (est.):** 70M instructions per main-thread frame × 2 TLB misses per 1000 instructions × ~60 cycles ≈ 3 ms at 2.8 GHz. Removing 70% of that is about 2 ms (8%). Memory cost: +100–300 MB.

**Prior art**
- [Borderlands 3 +8% with THP](https://blog.patshead.com/2023/02/enabling-transparent-hugepages-can-provide-huge-gaming-performance-improvements.html).
- [Temeraire, OSDI'21](https://www.usenix.org/conference/osdi21/presentation/hunter): +7.7% requests per second.

**Tier:** S. All games.

**Cheapest falsification:** measure per-thread data-TLB misses with `perf stat`, then A/B THP never / always / 16K. Kill if p50 frame time improves less than 2%.

**Biggest risk:** compaction stalls causing hitches.

### 5. Kill Wine's "syscall tax" and build a Deck-native Proton (rank 5)
**Mechanism**
- **The tax:** Proton 11's `QueryPerformanceCounter` (a timer games call constantly) goes `NtQueryPerformanceCounter` (`ntdll/time.c:383`) → `__wine_syscall_dispatcher`. The dispatcher saves the full AVX register state with `xsavec64` and restores it with `xrstor64` (`unix/signal_x86_64.c:3402–3409, 3533`) → `clock_gettime`. Windows does this in user mode with `rdtsc`.
- **Fast paths:** compute the timer on the Windows-DLL side from `rdtsc` plus shared data, and add spin budgets for `Sleep(0)`/`SwitchToThread`.
- **Build:** Proton compiles x86_64 with `-O2 -march=nocona` (`Makefile.in:55,59`), a 2004 SSE3 baseline. A Deck build would use `-march=znver2` + LTO + PGO.

**Budget math (est.):** a dispatcher round trip is about 100–160 ns versus about 15 ns native. At 10k calls per frame that's 1–1.5 ms of CPU. PGO+LTO gave RadeonSI 16–20% ([Phoronix](https://www.phoronix.com/news/Mesa-2020-PGO-LTO-Builds)); if the translation layers are 15% of the critical thread, that's about 2–3% of the frame.

**Tier:** I as a custom build. It becomes S if upstreamed into Valve's Proton.

**Cheapest falsification:** run `perf record` on three games and sum the % of cycles in the dispatcher, `ntdll.so` and the translation layers. Kill if it's under 3% on the critical thread.

**Biggest risk:** clock consistency across cores.

### 6. Per-pipeline shader-compiler (ACO) knob table (rank 6)
**Mechanism**
- Use RGP (`MESA_VK_TRACE=rgp`) to find the most expensive pipelines.
- Offline, recompile each with combinations of knobs: wave32/64 per stage, scheduler aggressiveness, unroll limits. Time each.
- Ship {hash → knobs} only, no game code. A small RADV patch reads the table, loaded through `VK_ICD_FILENAMES`.

**Budget math (est.):** if 15 pipelines take 70% of the GPU frame and tuning gains 7% on them, that's about 1.2 ms of a 25 ms frame.

**Prior art:** [RADV global wave switches](https://docs.mesa3d.org/envvars.html), Mesa driconf, vendor per-game shader profiles.

**Tier:** S (driver-level).

**Cheapest falsification:** an A/B of the existing global wave32 switches with RGP per-pipeline timings. Kill if none of the top 15 pipelines moves more than 5%.

**Biggest risk:** maintaining a custom Mesa build on SteamOS.

---

### Unknown unknowns
1. **SteamOS's RLIMIT_NICE.** One `cat /proc/<wineserver>/limits` tells us whether every game's `SetThreadPriority`, and DXVK's LOWEST compile threads, are silently no-ops today.
2. **GPU traffic inflating CPU latency.** Does GPU memory traffic raise CPU memory latency on Van Gogh? Run a pointer-chase on the CPU while a compute shader streams 60 GB/s. If latency doubles, saving GPU bandwidth directly speeds up CPU-bound frames.
3. **Missing L3 and the power-driver mode.** Chips and Cheese saw the L3 "basically missing" in latency tests under default SteamOS settings. We need to know whether SteamOS 3.8 runs the CPU frequency driver (amd-pstate) in active EPP mode. If so, `uclamp_min` frequency boosts do nothing, and only EPP works.
4. **Profiling limits.** Zen 2 has no branch-record hardware (LBR/BRS), so AutoFDO/BOLT profiles can't be sampled on the Deck. Proton's Windows-side DLLs also can't be processed by BOLT, which only handles Linux binaries. Profiles must come from a Zen 3/4 machine, or from instrumented builds made with llvm-mingw.
5. **Measurement can perturb or trip anti-cheat.** uprobes patch breakpoints into game memory, which anti-cheat may flag, so use sampling `perf` or ftrace on anti-cheat titles. **[Narrowed in Round 2: on anti-cheat titles use scheduler tracepoints or /proc counters only; stack-sampling perf copies user memory and is treated as risky (round2/X_anticheat_legal_maint.md).]**
