# W3 (CPU / fixed-cost wall): Round 3 report from the CPU-performance engineer

## Bottom line
- **Space Marine 2 (SM2) hordes are CPU-bound, and mainly limited by core count.** No S0/S1 lever closes that gap. The S0/S1-addressable part is about 1.3× at most, so hordes go from 14 to about 18 fps optimistic (est.). The real wall-breaker is Saber shipping a lighter swarm budget under `SteamDeck=1`.
- **Two of the asked-about levers already ship or aren't CPU levers:**
  - **ntsync is already the default on a stock Deck running Proton 11.** The SteamOS kernel config has `CONFIG_NTSYNC=m`. steamos-customizations-jupiter preloads the module (`misc/modules-load.d/ntsync.conf`, commit bb08ada, 2025-12-12). The upstream device is mode 0666 (linux v6.18 `drivers/misc/ntsync.c:1207-1212`). Proton 11's wineserver opens `/dev/ntsync` *before* fsync and switches fsync off (Proton wine `server/inproc_sync.c:48-66`, branch proton_11.0). Proton 9 and 10 have no ntsync at all.
  - **vkd3d-proton's descriptor heap is a correctness path, not a CPU path.** On RADV it already uses `EXT_descriptor_buffer` with memcpy `CopyDescriptors` variants (`resource.c:11355-11359`, `device.c:10442-10461`). The heap path is on by default only for WoW and NBA 2K27, to work around game bugs (`device_workarounds.c:134,215,225`).
- **New and worth bench time:**
  1. an S0 triage built on kernel counters, with no tracing;
  2. turning SM2's GPU slack into CPU watts, gated on throttle bits seen in CPU-bound samples;
  3. a "syscall-tax" trim: STIBP/retbleed/SRSO boot profiles and an ntsync vs fsync A/B;
  4. CPU-side pricing of game settings (Stalker 2 Engine.ini, the Wilds CPU tab).
  Each is worth about 0–15%.

## 1. Diagnosis: public evidence per scene

| Scene | Evidence | Likely cause |
|---|---|---|
| **SM2 hordes** | Deck: 14 fps; still under 30 at 640×400 ([SDHQ](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/)). PC: GPU busy 53% at 1080p Ultra; "Background Swarm Size" 3–5% ([PCOS](https://pcoptimizedsettings.com/warhammer-40k-space-marine-2-optimization-guide-best-graphics-settings-for-pc/)). Uses up to 12 threads; Ryzen 3 3100 (4C) "25+ fps" vs Ryzen 7 3700 (8C) "60+" ([GameGPU](https://en.gamegpu.com/action-/-fps-/-tps/warhammer-40-000-space-marine-2-test-gpu-cpu)). PS5 falls below 40 fps with dozens of enemies and is CPU-limited (DF via [multiplayer.it](https://multiplayer.it/notizie/warhammer-40000-space-marine-2-analizzato-digital-foundry-tps5-xbox-series-x-chiaro-vincitore.html)). Proton is not the problem on desktop: CachyOS 81 fps vs Windows 68 fps on a 5600X ([Notebookcheck](https://www.notebookcheck.com/Gaming-Test-CachyOS-uebertrifft-Windows-11-in-Cyberpunk-2077-Space-Marine-2-und-weiteren-Titeln.1263435.0.html)). | (a)+(b), limited by core count. (c)/(d) small. (e) not excluded on the Deck. |
| **Stalker 2 settlements** | Zalissya is "highly CPU-limited" on PC. v2.0 (UE 5.5.4): 84.6 → 120.1 fps average ([OC3D, 2026-08-21](https://overclock3d.net/reviews/software/stalker-2-patch-2-0-tested-huge-improvements/)). No Deck settlement data exists. | (a), GameThread (est.) |
| **MH Wilds plains/camps** | Deck: "more related to the GPU than the CPU" (SDHQ 1.040). The base-camp CPU bug (claimed-content checks) was fixed on 2026-01-28, which also added a **CPU tab** to Options ([VGC](https://www.videogameschronicle.com/news/monster-hunter-wilds-gets-a-pc-patch-which-capcom-says-will-fix-the-recently-reported-dlc-performance-bug), [FinalWeapon](https://finalweapon.net/2026/01/27/monster-hunter-wilds-update-1-040-03-01-patch-notes/)). I could not verify the CPU tab's contents: Capcom's notes page was blocked. | Plains: (e)/GPU. Camps: (a) (est.) |

**Corrections to the brief:**
- **MangoHud has no per-frame GPU/CPU split.** Its in-process layer must not be used on SM2. Valve's out-of-process `mangoapp` logs frame time and GPU load (`src/app/main.cpp:128-141`).
- **Round 2's "free High GPU settings on SM2" holds only for cause (a).** Under (b), shadows and draw distance add render-thread CPU.

## 2. Status of the candidate levers you named

- **Descriptor heap.**
  - It is an opt-in: `VKD3D_CONFIG=descriptor_heap`, plus `RADV_EXPERIMENTAL=heap` on SteamOS's RADV.
  - That RADV is a 26.2-devel snapshot, tag `steamos-26.05.19` (PKGBUILDs-mirror `jupiter-3.9/mesa-radv`). It predates RADV's default flip on 2026-06-29 ([Phoronix](https://phoronix.com/news/RADV-Descriptor-Heap-Default)).
  - No CPU measurement has been published ([Phoronix](https://phoronix.com/news/vkd3d-proton-descriptor-heaps)). Expected gain on RADV: 0–2% (est.). It already sits in Round 2's F2 sweep, so it is **not new**.
  - Stable 3.8's Mesa version: could not verify.
- **ntsync.** Already on by default (see bottom line). The reverse switch, `PROTON_NO_NTSYNC=1`, is documented in Proton's README (`README.md:325-326`).
- **Submission threading.** vkd3d always submits from its own `vkd3d_queue` thread (`command.c:26227`); command lists are recorded on the game's threads. There is no new flag beyond F2's. DXVK doesn't apply: all three games are D3D12.
- **SMT off.** Already covered by C. For SM2 it should be negative: low-core CPUs without SMT "had MAJOR stuttering" ([DSOGaming](https://www.dsogaming.com/pc-performance-analyses/warhammer-40k-space-marine-2-benchmarks-pc-performance-analysis/)).
- **Frame cap / refresh divisor.** Already shipping in the Quick Access Menu.

## 3. Ideas

### Idea 1: "Four-counter triage" (S0, no tracing)
1. **Pitch:** sort each scene into (a)–(e) using only kernel metadata files and Valve's own UI knobs.
2. **Already done?**
   - Round 2's G0 uses `perf sched`, which is tracing and only "safe-likely" on EAC. It has no per-process GPU time.
   - Nobody publishes per-thread `run_delay` or fdinfo GPU-time triage for Proton.
3. **Mechanism.** Sample at 50 Hz:
   - `/proc/<pid>/task/*/schedstat`: run ns, runqueue wait ns, slices. The kernel has `CONFIG_SCHED_INFO=y` and `SCHEDSTATS=y`.
   - Per-thread `stat` stime vs utime, plus `comm`. Thread names include `vkd3d_queue`, `vkd3d_fence`, and UE's GameThread, RenderThread and RHIThread.
   - Wineserver CPU time.
   - `/proc/<pid>/fdinfo` `drm-engine-gfx` ns, the per-process GPU busy time (`amdgpu_fdinfo.c:121`).
   - `gpu_metrics` (`vangogh_ppt.c:1682-1705`).
   - Then a 2×2 clock test: `scaling_max_freq` 3.5/2.8 GHz × Steam's GPU slider 1600/1100 MHz. A CPU-bound scene has CPU elasticity ≥0.4 and GPU elasticity ≤0.1. Fixed-cost GPU (e) shows GPU elasticity ≥0.5 at 640×400.
   - A (b)-vs-(c) split on SM2 is possible only via `VKD3D_QUEUE_PROFILE`, an undocumented stock env var (`queue_timeline.c:33`; it records command-list reset→close spans and submit overhead). Treat it as S1-caution.
   - On Stalker 2 and Wilds, IP-only `perf record` (no call graphs) measures the share spent in vkd3d, ntdll and RADV. Use that as a prior for SM2.
4. **Tier:** S0. `VKD3D_QUEUE_PROFILE` is S1.
5. **Budget:** 0 fps directly. Overhead: 40 threads × 50 Hz × ~3 µs ≈ 6 ms/s, about 0.1% of the APU (est.). Its value is stopping spend on the wrong lever.
6. **Red team:** "It's only telemetry." Answer: it is the only S0 way to separate (e) from (a)/(b) at fixed resolution, and it reprices every W3 lever.
7. **Maintenance:** kernel ABI counters are stable. Thread-name maps change with game patches; DeckForge owns them.
8. **Falsification (3 days):**
   - Controls: Civ VI (CPU-bound) and Wukong Low 50% (GPU-bound), 10 runs each.
   - **Pass:** both controls classified correctly in ≥9/10 runs, and elasticity 95% CI width ≤0.1.
   - **Kill:** a control is misclassified, or the counters cost >1% fps.

### Idea 2: Spend SM2's GPU slack on CPU watts
1. **Pitch:** in scenes that stay CPU-bound, a per-game GPU clock ceiling lets the SMU raise CPU clocks.
2. **Already done?**
   - Round 2 killed watt arbitrage in *GPU-bound* frames and gated its GPU-cap arm on GPU-bound samples. Round 1's per-frame version died with the frame-phase governor.
   - No guide sets a GPU cap for CPU-bound fps.
3. **Mechanism:** Steam's own Manual GPU Clock slider (steamos-manager `gpu.rs:371`). It helps only if SPL/FPPT/SPPT throttle bits fire while TDC_VDD (CPU rail current) doesn't (`vangogh_ppt.c:218-230`).
4. **Tier:** S0.
5. **Budget** (SM2 horde, 71 ms per frame):
   - Pessimistic: throttle bits don't fire → 0.
   - Central: 3.0 → 3.3 GHz with a 0.55 clock-sensitive share → 0.45 + 0.55 × 0.909 = 0.95 → 14.8 fps (+5%).
   - Optimistic: 2.7 → 3.4 GHz with a 0.65 share → 0.866 → 16.3 fps (+16%).
   - This draws on the same power pool as Round 2's undervolt and guided mode. Count only the increment.
6. **Red team:** it competes with E for the same GPU slack: watts vs image quality. Answer: that is a Pareto choice, and the experiment measures both sides.
7. **Maintenance:** one per-game value in Valve's own profile. Re-validate after SMU or kernel updates (20 minutes).
8. **Falsification (1 week):** 10 interleaved runs of a fixed horde set-piece.
   - Gate: in samples with GFX activity <80%, power-limit bits are set ≥30% of the time and TDC_VDD <10%.
   - Then test caps of auto / 1100 / 900 MHz.
   - **Pass:** core clock +≥8% and median frame time −≥4%, with GPU busy <90%.
   - **Kill:** power-limit bits <20%, or median frame time improves <2%.

### Idea 3: Syscall-tax trim (mitigation profile + sync-primitive A/B)
1. **Pitch:** Zen 2 pays for retbleed and SRSO on every kernel `ret`, and ntsync makes every sync operation an ioctl.
2. **Already done?**
   - SteamOS's command line has no `mitigations=` (jupiter-hw-support `etc/default/grub-steamos:16-27`). The kernel builds UNRET, SRSO and RETBLEED mitigations in.
   - Under retbleed's `unret` mode, the kernel forces "STIBP always-on" whenever SMT is active (linux v6.18 `bugs.c:1994-2001` and `2471-2485`). That costs user code too.
   - Not in Round 2.
3. **Mechanism:** compare three boots on the bench Deck: default, `spectre_v2_user=off` (drops STIBP only), and `mitigations=off`. Separately, A/B `PROTON_NO_NTSYNC=1`. fsync skips the syscall on uncontended operations (`fsync.c:549-550`).
4. **Tier:** S0 for the boot profiles, S1 for the env var. The boot profiles carry a security risk (steamwebhelper runs web JavaScript), so they are bench-only unless the narrow `spectre_v2_user=off` arm alone carries the gain.
5. **Budget:** saving = kernel share k × m / (1 + m), where m is the mitigation inflation of kernel time.
   - Pessimistic: k = 4%, m = 15% → 0.5%, effectively 0.
   - Central: k = 8%, m = 40% → +2%.
   - Optimistic: k = 12%, m = 60% → 4.5%, plus STIBP 3% → +7.5%.
   - SM2: 14 → 14.3 / 15.0. ntsync vs fsync: ±0–3% either way.
   - The only Zen 2 data point is general: default mitigations cost 5.4% geomean on a 3950X ([Phoronix](https://www.phoronix.com/review/amd-3950x-retbleed/5)).
6. **Red team:** "Games barely move with mitigations." Answer: those were native, low-syscall games. A kill gate on kernel-time share makes this cheap to abandon.
7. **Maintenance:** `/etc/default/grub` should persist across updates (est.). Re-check `/sys/devices/system/cpu/vulnerabilities/*` after each kernel bump.
8. **Falsification (1 week):**
   - Day 1: syscall micro-benchmark under each boot.
   - Gate: the game's stime share, measured with Idea 1. **Kill** if it is <5% in every scene.
   - **Pass:** −3% median or −5% p99 frame time in at least one CPU-bound scene, with the CI excluding 0.

### Idea 4: CPU column for the price list
1. **Pitch:** price settings by critical-thread milliseconds, not GPU milliseconds.
2. **Already done?** E's budget gives nothing in CPU-bound frames. This is **E's missing column, to be merged into E's table, not added to E's GPU gain.**
3. **Mechanism:**
   - **Stalker 2** (no anti-cheat), Engine.ini: `a.URO.ForceAnimRate`, `r.SkeletalMeshLODBias`, `r.ViewDistanceScale`, `grass.DensityScale`, `r.Shadow.CSM.MaxCascades`.
   - **Wilds:** the CPU-tab items, plus "Background Frame Rate" (animation halving, per a [Steam thread](https://steamcommunity.com/app/2246340/discussions/0/596270875262608495)).
   - **SM2:** the menu settings are already Low under `SteamDeck=1`. Keep the default FOV: a FOV of 1.45 costs 5–6% (PCOS).
4. **Tier:** S (settings files).
5. **Budget:**
   - Stalker 2 settlements at 28 fps central: −2 / −10 / −20% CPU frame time → 28.6 / 31.1 / 35 fps.
   - Wilds camps: 0 / +5 / +15%.
   - SM2: 0.
6. **Red team:** shipping builds ignore cvars flagged `ECVF_Cheat`. Check each cvar in the game log, and drop any that don't apply.
7. **Maintenance:** Engine.ini files survive game patches. Re-check after each UE version bump.
8. **Falsification (1 week):**
   - Fixed Zalissya route, 10 runs per arm.
   - **Pass:** −8% GameThread milliseconds at ≤0.1 JOD loss.
   - **Kill:** <3% saving.

## 4. Wall-breaker: is there an S0/S1 way to make SM2 cheaper?
The gap from PS5 (~38 fps) to the Deck (14 fps) is 2.7×. My decomposition (all est.):
- cores: 1.8× (~8.1 vs ~4.5 core-equivalents);
- clock under 15 W: 1.17×;
- L3 size and DRAM latency: 1.1×;
- PC-port overhead: 1.15×.

Only the clock factor and a slice of the overhead are reachable at S0/S1, about 1.3× at best. **No S0/S1 wall-breaker exists for SM2 hordes.** The durable path is upstream: ask Focus/Saber, through the X3 channel from Round 2, to add a 4-core swarm and AI budget to `SteamDeck=1`. For Wilds and Stalker 2, Idea 4 is the closest thing to a wall-breaker.

## 5. Unknown unknowns
1. **The Deck has no VRR.** Under FIFO, presented frame times are quantised to refresh steps, so A/B gains smaller than one refresh interval disappear. Measure with tearing allowed, or from vkd3d's present timestamps.
2. **Non-game CPU use on 4 cores.** steamwebhelper, Steam's background `fossilize_replay` and mangoapp may take 0.3–0.5 of a core during play. Measure it during a horde.
3. **L3 clock.** On Zen 2 the L3 clock follows the core clocks. Log `current_l3clk` (`vangogh_ppt.c:1703`): CPU-bound frames may be L3-clock-bound rather than core-bound.

## Checked facts dated after June 2026
**Verified:**
- RADV heap default flip.
- vkd3d-proton heap: merged 2026-05-27; per-game enables 2026-07-10 (WoW) and 2026-10-05 (NBA 2K27), confirmed in git.
- Proton 11.0 stable on 2026-07-07 ([comss](https://www.comss.ru/page.php?id=21187)).
- SteamOS 3.9 preview on kernel 7.2 ([Phoronix](https://phoronix.com/news/SteamOS-3.9-Preview)).
- Stalker 2 v2.0 Zalissya numbers (OC3D).

**Correction to Round 2:** SteamOS's RADV package already builds Mesa's `anti-lag` layer (`mesa-radv` PKGBUILD, line 281).

**Could not reach:** info.monsterhunter.com and PCGamingWiki (permission timeouts); gitlab.freedesktop.org (proxy 403).

## Key facts to keep
- Proton 11 uses ntsync by default on SteamOS; `PROTON_NO_NTSYNC=1` falls back to fsync.
- vkd3d-proton uses descriptor buffers on RADV; its descriptor heap is opt-in and needs `RADV_EXPERIMENTAL=heap` on SteamOS's May 2026 RADV snapshot.
- SteamOS runs default CPU mitigations, which means STIBP always-on while SMT is active.
- Wilds has had a CPU tab in Options since 2026-01-28.
- SM2 hordes are core-count-bound; there is no S0/S1 path to 30 fps native.

Local working files: `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/r3w3/`.
