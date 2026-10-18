# Hardware, power and thermal angle: 7 ideas, ranked by my confidence

**What the evidence says before the ideas.** CPU, GPU and SoC share one 15 W budget, and a watt the CPU wastes is a watt the GPU loses.
- In GPU-bound work the GPU takes more than 10 W and the CPU gets 2–3 W at "cell-phone clocks". The CPU takes about 1 s to reach its top clock. ([Chips and Cheese](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu); LCD Deck.)
- Memory bandwidth limits more than GPU clock does:
  - Raising LCD memory from 5500 to 6400 MT/s (+16% bandwidth) gave +5–6% fps with "no extra power" ([hardforum](https://www.hardforum.com/threads/steam-deck-overclock-undervolt-results.2030124/)).
  - Raising the GPU from 1.6 to 2.0 GHz at 23 W (+25% clock) gave only +5–9% average fps ([SDHQ](https://steamdeckhq.com/news/undervolting-and-overclocking-push-your-steam-deck-beyond-its-limits/)).
  - So fps rises about 0.35% per 1% of bandwidth, against about 0.2–0.36% per 1% of GPU clock.
- The 6 nm OLED chip needs about 12–13 W to match the LCD at 15 W ([willett.io](https://www.willett.io/posts/watts/), citing a video). So on the OLED the 1.6 GHz GPU clock cap is often the limit before the power cap is.

## 1. Watt arbitrage: slow down the CPU work that doesn't set frame time, and feed the GPU
- **Mechanism:**
  - Find the threads that set frame time using only kernel tracepoints: the chain of `sched_wakeup` events ending at the thread that submits GPU work. Nothing is attached to the game process.
  - A sched_ext scheduler policy, similar to LAVD, keeps those threads on 2 cores at full clock.
  - The other cores get a per-core clock cap. Van Gogh's amdgpu driver supports this directly: `pp_od_clk_voltage` "p core 1 MHz" sends SetSoftMaxCclk with the core ID (vangogh_ppt.c L2035–2165; allowed range 1400–3500 MHz, L2188–2189). Manual mode is required (L2041).
  - The firmware already shares power by demand, so the freed watts go to the GPU on their own.
- **Why it beats the wall:** the firmware cannot tell a worker core that is spin-waiting from one doing work the frame needs.
- **Budget math:** a mixed CPU+GPU scene might split CPU 5 + GPU 8 + SoC 2 W (est.). Freeing 1.5 W raises GPU power to 9.5 W (+19%). If GPU power grows with clock^2.5 (est.), clock rises about 7%, which gives +2.5–7% fps depending on bandwidth limits. If the GPU is already at its 1.6 GHz cap, the 1.5 W goes to battery instead.
- **Tools:** scx_lavd, `perf sched`/bpftrace on tracepoints, and gpu_metrics, which reports per-core power (`average_core_power[]`, L1693), `average_gfx_power` and `throttle_status`.
- **Prior art:**
  - LAVD on Deck OLED, Tomb Raider benchmark: 12.7 W fell to 10.7 W (−16% energy) ([LPC 2024](https://lpc.events/event/18/contributions/1713/attachments/1425/3058/scx_lavd-lpc-mc-24.pdf)).
  - Vernet's amd-pstate `epp_boost` patch: 1% lows up to +31.8% in Civ VI on the Deck ([SDHQ](https://steamdeckhq.com/news/linux-patches-boost-1-low-framerates-steam-deck/)).
- **Tier:** S. Applies to all games; the largest gains should be in CPU-heavy titles like Stalker 2, MH Wilds and Space Marine 2.
- **Falsification (1 week, bench Deck):**
  - At a fixed 15 W, sweep the all-core CPU clock cap {3.5, 3.0, 2.6, 2.2 GHz} × SMT on/off × default scheduler/LAVD, on 5 fixed-camera scenes.
  - Log fps, p99 frame time and GPU power and clock 10 times a second.
  - Kill it if no setting gives ≥5% average fps or ≥10% better p99, or if GPU power doesn't rise when CPU power falls.
- **Biggest risk:** engines with sync points wait on the slowest worker, so slowing workers can lengthen the frame.

## 2. Frame-deadline governor: pace the GPU to the deadline instead of racing then idling
- **Mechanism:**
  - A system daemon reads present times from gamescope and GPU busy time from gpu_metrics.
  - Every few frames it sets the GPU's minimum and maximum clock to the lowest clock that keeps p99 under 22.2 ms with a margin.
  - It holds the CPU minimum clock high on the critical cores, which skips the roughly 1 s ramp.
  - It also tries Van Gogh's undocumented CAPPED power profile: `pp_power_profile_mode` 8 ([commit 31865e96](https://lab.nexedi.com/kirr/linux/-/commit/31865e96f9eb52ced6d5e23f9f3a5376f81c9410)).
- **Why it beats the wall:** dynamic energy per frame scales with voltage squared. The default power management races to 1.6 GHz, idles, and reacts to averaged load.
- **Budget math:** suppose the GPU is busy 16 ms per frame at 1.6 GHz. The same work fills 20 ms at 1.28 GHz. If voltage drops from 1.00 to 0.85 V (est.), energy per frame falls to 0.85² = 0.72, a 28% cut. That is about 2 W of roughly 7 W GPU dynamic power (est.), freed for the CPU or battery. Memory-bound work doesn't slow with clock, which helps.
- **Prior art:** [Pathania DAC'14](https://www.comp.nus.edu.sg/~tulika/DAC14.pdf): up to 26% less power than Linux's default governors at comparable fps (Exynos 5410). AMD's Radeon Chill and `epp_boost` work on the same principle.
- **Tier:** S. Applies to any frame-capped game.
- **Falsification (≤2 weeks):** first find the best possible static setting. Sweep a locked GPU clock in 100 MHz steps on 3 capped scenes and find the lowest clock with p99 under 22.2 ms. If that saves less than 1 W, or doesn't improve p99, a dynamic controller cannot win, so kill it.
- **Biggest risk:** scene changes faster than the control loop cause missed frames, and Steam's own GPU clock slider may fight the daemon.

## 3. Per-unit undervolt search with error checking
- **Mechanism:**
  - Valve's BIOS 118+ offers CPU, GPU and SoC voltage offsets from 0 to −50 mV in 10 mV steps ([HotHardware](https://hothardware.com/news/steam-deck-undervolting-how-to-access-them)). OLED owners report the same menu ([Steam forum](https://steamcommunity.com/app/1675200/discussions/0/4040357120668252133)).
  - DeckForge must not write BIOS settings itself. Instead it guides the user: the user sets an offset, then DeckForge runs a 20-minute test. The test uses GPU and CPU kernels with known bit-exact answers, plus fps and true-clock measurement (APERF/MPERF).
  - It bisects to the best stable offset, then keeps a 10 mV safety margin.
- **Why it beats the wall:** AMD sets voltages for its worst chips. Under a fixed power cap, spare voltage margin becomes extra clock.
- **Budget math:** going from 0.95 to 0.92 V (est.) cuts dynamic power about 6%. Measured results:
  - GPU drew 1–2 W less (SDHQ).
  - OLED at −20/−50/−50 performed at 9 W like stock at 10 W, and +4% at 10 W ([lemmy](https://lemmy.linuxuserspace.show/post/163057)).
  - Battery life +14–16% (HotHardware; SDHQ).
  - Expected at 15 W: +1–3% fps, or the watts go to the CPU or battery if the GPU is at its clock cap.
- **Tier:** S (a user-set firmware option). All games.
- **Falsification (1 week, 3 Decks):** test offsets {0, −20, −40} at 15 W and 10 W. Kill it if fps gains are under 2% at 10 W and power savings at equal fps are under 1 W.
- **Biggest risk:** silent data corruption, including save files. OLED users report SoC offsets below −10 crash. At −50 mV the CPU can slow itself down without crashing ("weird slowdowns"). Warranty risk is low because the menu is official, and a CMOS reset recovers a bad setting.

## 4. Memory clock: never trade bandwidth for GPU watts, and pin the memory and fabric clock high
- **Mechanism:**
  - For each scene, force the highest memory and fabric clock state through `pp_dpm_fclk`/`pp_dpm_mclk` (vangogh_ppt.c L1203–1220). This prevents downshifts that raise CPU memory latency (already about 150 ns per Chips and Cheese) and cut GPU bandwidth.
  - Drop one step only in scenes measured as compute-bound.
- **Budget math:** the SoC rail (`average_soc_power`) probably draws 1.5–3 W (est.). One step down saves 0.5–1 W (est.), which is about +1% fps in a compute-bound scene. In a bandwidth-bound scene, −15% bandwidth costs about −5% fps. So pinning high wins by default.
- **Tier:** S for clock pinning. Memory overclocking is a hardware mod (unofficial BIOS editors). On the LCD it gave +5–6%, but needed power-down disabled and games occasionally failed to load. OLED at 7000+ MT/s would give an estimated +3–4%; research only.
- **Falsification (3 days):** force the lowest and highest states on 5 scenes plus a bandwidth microbenchmark. Measure fps, SoC power and CPU frame time.
- **Biggest risk:** the display engine may block or force these clock switches, causing underflow or flicker.

## 5. Find hidden thermal throttling, then add a forced-air accessory
- **Mechanism:**
  - Log the `throttle_status` bits during 30–60 minute sessions at 20 °C and 35 °C room temperature. The thermal bits (THM_CORE/GFX/SOC) are distinct from the power-limit bits (SPPT/FPPT) (L222–235).
  - If the thermal bits fire, use a fan-curve profile (Tier S) and/or a clip-on blower with its own battery, so its power is outside the APU budget.
- **Budget math:**
  - Leakage is probably 1.5–3 W near 90 °C, and a 20 °C drop cuts it 30–40% (est.). That frees 0.5–1.2 W, about +1–4% clock.
  - Measured: an LCD Deck with a cooler backplate (−5 °C) gained +6% average and +17–19% lows in Returnal at stock clocks ([SDHQ](https://steamdeckhq.com/news/how-low-can-it-go-steam-deck-thermal-modding/)). That is too big for leakage alone, so it suggests real thermal limits are firing.
  - A clip-on fan plus a PTM7950 pad cut temperatures 18–20 °C.
  - A Peltier cooler doesn't work: it needs about 2× the heat it pumps, so 30 W or more.
- **Tier:** accessory (fan curve is Tier S). Matters for long sessions and hot climates.
- **Falsification (1 week):** 3 games × {stock, max fan, clip-on fan} × {20, 35 °C}, fixed 15 W. Kill it if the thermal bits never fire and the fps difference is under 2%.
- **Biggest risk:** the OLED may already run cool enough, so the gain is only noise and battery.

## 6. Tethered handheld: battery grip with power pass-through plus a raised power limit (research only)
- **Mechanism:** a grip with a battery or 45 W power supply keeps the Deck on wall power in the hand, combined with a BIOS-unlocked 18–23 W limit.
- **Evidence:**
  - The kernel driver accepts limits up to 29 W sustained and 30 W short-term (L2377). The firmware clamps to the BIOS value.
  - An unofficial BIOS patch reached 18 W on the OLED (willett.io). LCD Decks sustained 21–23 W.
  - Going from 15 to 18–23 W gave "maybe +5%" (hardforum).
  - Undervolt plus overclock at 23 W in Cyberpunk: +7–9% average, +16% 1% lows, +27% 0.1% lows (SDHQ).
  - On the OLED the extra watts mostly feed the CPU, which suits CPU-heavy PS5-era games.
- **Budget math:** APU 20 W + about 8 W for the rest of the system (est.) = 28 W, so the 50 Wh battery alone lasts about 1.8 h.
- **Tier:** hardware/firmware mod. Risks: brick, weak VRM (3 stages per Chips and Cheese), current-limit throttling, and likely warranty denial. Not shippable under DeckForge's rules.
- **Falsification:** on one sacrificial bench Deck, compare 15 W and 20 W on 5 CPU-heavy scenes. Kill it if p99 improves by less than 10%.
- **Biggest risk:** hardware damage.

## 7. USB co-processor for work outside the 15 W budget (mostly negative)
- **Why it seemed promising:** an accessory's power isn't counted in the APU limit. A [Coral stick](https://www.coral.ai/static/files/Coral-Accelerator-Module-datasheet.pdf) gives 4 TOPS INT8 at 2 TOPS/W (MobileNet v2 in 2.4 ms). That compares with the Deck GPU's INT8 peak of 8 CUs × 64 lanes × 8 ops × 1.6 GHz ≈ 6.5 TOPS (est.).
- **Why it fails for frames:**
  - USB 3.2 Gen 2 delivers about 1.0 GB/s in practice (est.). One 1280×800 frame is 4.1 MB, so 4 ms each way. A round trip of 8 ms or more, plus inference, plus a frame of latency rules out per-frame pixel work.
  - Hailo-8-class NPUs need PCIe, and the Deck has no USB4/Thunderbolt PCIe tunneling.
  - Offloading a game's audio or decompression needs Tier I hooks, for less than 0.5 W (est.).
- **What survives:** running DeckForge's own control-loop models (scene classifier, quality estimator) on the stick, saving 0.2–0.5 W (est.).
- **Falsification:** measure the DeckForge daemon's per-core power. Kill it if under 0.3 W.
- **Tier:** accessory.

## Unknown unknowns
1. **Cold can be less stable than hot.** At low voltage, FinFET logic gets *faster* when hot ([ISLPED'14](https://coldflux.usc.edu/~massoud/Papers/DTM-FinFET-TempEffeInv-islped14.pdf)). An undervolt tuned on a warm Deck can fail on a cold boot or in winter. Test stability at 10 °C and 40 °C.
2. **Steam may silently undo DeckForge's settings.** The Steam client (or steamos-manager) may rewrite the performance level, `pp_od_clk_voltage` and power caps when a game launches or Quick Access settings change. Manual mode also changes GPU clock management. Read the values back every second.
3. **Nobody logs which limit actually binds.** It could be the sustained power limit (power1_cap), the short-term limit (power2_cap), SPL/STAPM, or the TDC current limits. The `throttle_status` bits say which.
4. **The CAPPED/UNCAPPED profiles are untested.** They are Van Gogh-only and their commit doesn't say what they do. Testing one costs a single sysfs write.
5. **Power-state exit delays may set p99 more than throughput does.** Candidates are GPU power-off between capped frames, CPU sleep states, and the roughly 1 s CPU ramp.

All experiments above go on the bench runner's dedicated Deck, never a personal unit (R7). Driver citations refer to `drivers/gpu/drm/amd/pm/swsmu/smu11/vangogh_ppt.c` in mainline Linux as of 2026-10-18.
