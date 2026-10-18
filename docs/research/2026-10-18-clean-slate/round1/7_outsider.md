**Outsider report: 6 ideas, ranked by how much I believe in them**

Common thread: under the brief's rules, everything *below* the game (the kernel, the Mesa driver, the gamescope compositor) is Tier S and open source. That layer is where phone makers and GPU vendors get their wins, and PC modding culture rarely looks there. Linked items are measured facts; (est.) marks my estimates.

---

### 1. Deadline-aware CPU/GPU clocking ("Android's performance hints for Proton")

**Pitch:** Part of the 1%-low wall is a control-loop bug. The governors that set clock speeds react over hundreds of ms, while a frame lasts 22–33 ms. Give them the frame deadline.

- **Mechanism:**
  - Two places already know the target frame period and each frame's CPU submit time:
    - gamescope, which runs outside the game process;
    - Mesa 26.3's new driver-side `vk_frame_pacer`, Valve's work for VK_AMD_anti_lag ([Phoronix, Oct 2026](https://phoronix.com/news/Mesa-26.3-RADV-VK_AMD_anti_lag)).
  - Export Android-style "target vs actual work duration" hints from there. They go to a sched_ext scheduler policy (the LAVD scheduler is supported in [SteamOS 3.8](https://phoronix.com/news/SteamOS-3.8.10-Stable)) and to the amd-pstate energy-performance preference (EPP).
  - Raise clocks for the render/game threads *before* their predicted burst, predicting from the last N frames (MPC-style).
  - When a frame has slack, run non-critical worker threads at their most efficient clock.
  - CPU and GPU share one 15 W cap, so every CPU watt not wasted sprinting to idle goes to the GPU. This is the time-domain half of the "power steering" already in the base.
- **Why it beats the wall (measured):**
  - The Deck CPU takes about 1 s to reach max boost; Renoir takes 9 ms ([Chips and Cheese](https://old.chipsandcheese.com/2023/03/05/van-gogh-amds-steam-deck-apu/)).
  - Render threads sleep briefly every frame, which decays the hardware's performance signal ([PC Gamer](https://www.pcgamer.com/hardware/handheld-gaming-pcs/linux-kernel-patch-can-boost-the-steam-decks-1-percent-low-frame-rate-by-as-much-as-31-percent-in-early-testing/)).
  - A Godot developer measured the Deck GPU dropping to 200–300 MHz under bursty compute load and getting 20–30 fps. Pinning it at 500–600 MHz gave 60 fps ([forum, Mar 2026](https://forum.godotengine.org/t/peaky-gpu-load-causes-steamdeck-to-set-its-gpu-clock-too-low-causing-poor-performance/135264)).
- **Budget math:**
  - Measured: a heuristic EPP boost alone gave +31.8% 1% lows and 4.1% better frame times (Civ VI, early results).
  - Power side: the CPU averages about 4 W (est.). Saving 0.5–1 W moves the GPU from 9 W to about 10 W. Near the top of the voltage/frequency curve (P ∝ f·V²) that is about +4% GPU clock, or about +3% fps in GPU-bound scenes (est.).
  - Cost of boosting: bursts take ~5% of the time × +3 W ≈ +0.15 W on average (est.).
- **Tools:** sched_ext/scx_lavd, the `amd_pstate.epp_boost` patch, uclamp, bpftrace, gamescope timestamps.
- **Prior art:**
  - [Android ADPF Performance Hint API](https://source.android.com/docs/core/perf/performance-hint-api); its docs say a governor takes about 200 ms to ramp.
  - [Pillai & Shin, real-time DVFS, SOSP 2001](https://www.sosp.org/2001/papers/pillai.pdf).
  - David Vernet (Meta) proposed it at Linux Plumbers 2026, including "thread hints from Wine/Proton" ([Phoronix](https://www.phoronix.com/news/Boost-Recently-Busy-CPUs)).
  - [LWN on LAVD](https://lwn.net/Articles/1051430/): one player action involves 20–30 cooperating tasks.
- **Tier S.** Applies to all games, most of all CPU-bound ones (Wilds hubs, Space Marine 2 hordes, Stalker 2).
- **Cheapest falsification (≤1 week):**
  - Bench Deck running a kernel with epp_boost.
  - 10 runs of each configuration: stock; epp_boost; epp_boost + LAVD; epp_boost + uclamp_min on the render threads. Use the Wilds benchmark and Space Marine 2.
  - Measure 1% and 0.1% low frame times from gamescope timestamps, and energy per frame from battery sysfs.
  - Kill if 1% lows improve less than 5% in both games, or energy per frame rises more than 5%.
- **Biggest risk:** it only helps frames limited by sleep/wake patterns. Games that saturate every core gain nothing.

### 2. Driver-forced variable rate shading (the shading dial Valve already built for the Deck's chip)

**Pitch:** RDNA2 has hardware variable rate shading (VRS). The RADV driver can force it on games that never asked for it, change it live, and it stays Tier S.

- **Mechanism:**
  - `RADV_FORCE_VRS=2x2|2x1|1x2` shades in coarse blocks for every pipeline that doesn't use VRS itself.
  - `RADV_FORCE_VRS_CONFIG_FILE` changes the rate live. The docs say it "only affects GFX10.3 APUs", which is the Deck's chip ([Mesa envvars](https://docs.mesa3d.org/envvars.html)). Valve wrote it in 2022, aimed at power savings ([Phoronix](https://www.phoronix.com/news/RADV-Dynamic-VRS)).
  - Step 2 is a small Mesa patch borrowed from emulators. RPCS3 and Dolphin choose which surfaces to scale by their size. Here, coarse-shade only render targets at the internal (pre-upscaler) resolution, never ones at output resolution, so the HUD and post-processing stay sharp.
  - Step 3: vary the rate with motion and contrast, the way video codecs vary quantization.
- **Why:** coarse shading cuts pixel-shader work up to 4×. Visual masking hides it in moving, textured and dark areas, and the upscaler's jitter partly re-samples the lost detail.
- **Budget math:**
  - Pixel-shader-bound work is 15–35% of a 33 ms GPU frame (est.), so 5–11.5 ms.
  - 2×2 saves about 40–50% of that, because helper lanes and render-target bandwidth don't shrink (est.). That's 2–5.8 ms, or +6–21% fps (est.).
  - Measured elsewhere: "upwards of 30%" at 4K on desktop RDNA2 ([Phoronix](https://www.phoronix.com/news/RADV-Render-Less)); NVIDIA Adaptive Shading "up to 15%" ([NVIDIA](https://www.nvidia.com/en-us/geforce/news/nvidia-adaptive-shading-a-deep-dive)).
  - No extra memory, and power goes down.
- **Tier S.** Best for engines heavy on pixel shaders. Engines that light the scene in compute shaders (Unreal's Lumen, Remedy's Northlight in Alan Wake 2) gain little.
- **Cheapest falsification (1 evening):**
  - Launch with `RADV_FORCE_VRS=2x2 %command%` on the Wilds benchmark, the [Wukong benchmark](https://store.steampowered.com/app/3132990/Black_Myth_Wukong_Benchmark_Tool/) and Space Marine 2.
  - Measure GPU frame time, plus ColorVideoVDP and FLIP scores at the Deck's viewing geometry.
  - Kill rule: VRS must cost fewer perceptual quality units (JOD) per ms saved than simply lowering the render scale by the same ms.
- **Biggest risk:** blurred HUD text and bad interaction with the upscaler until the size-filter patch exists.

### 3. A perceptual price list (an economist's settings menu)

**Pitch:** Give every setting a price in ms and a value in JOD, measured at the Deck's real viewing geometry. Then buy settings by the economist's equal-marginal-value rule until the budget (22.2 or 33.3 ms) is spent.

- **Mechanism:**
  - Cost (Δms) per setting comes from per-pass GPU timings on the Deck (RGP via RADV thread trace).
  - Quality change (ΔJOD) comes from [ColorVideoVDP](https://github.com/gfxdisp/ColorVideoVDP) with a custom Deck display model: 7.4", 1280×800, Fede's measured viewing distance, the OLED's peak brightness and black level, room lighting.
  - Fill the budget greedily and re-measure settings that interact. Render scale and VRS are just more items on the menu.
  - HDR costs about 0 ms on the OLED but needs a human A/B, because ColorVideoVDP needs a reference with the same dynamic range.
  - Optional add-on: blue-noise grain in gamescope (about 0.05 ms, est.). Added noise measurably raises perceived sharpness ([Kurihara et al., SPIE 2009](https://ebooks.spiedigitallibrary.org/conference-proceedings-of-spie/7240/724014/Analysis-of-sharpness-increase-by-image-noise/10.1117/12.806078.full)).
- **Why:**
  - At 30 cm the Deck shows 0.30 m × tan 1° × 1280 px / 0.1594 m = **42 pixels per degree** (56 at 40 cm). The finest detail it can show is about 21 cycles per degree.
  - A 0.75× render scale loses only the 16–21 cycles-per-degree band. The eye is several times less sensitive there than at 2–5 cycles per degree (est., from the contrast sensitivity curve). The 2–5 band is where AO, shadow, global illumination and tone errors show up.
  - Reconstruction beats raw pixels: Digital Foundry rated RE Requiem on Switch 2 (540p + DLSS) above Series S at 720p ([Pure Xbox](https://www.purexbox.com/news/2026/02/digital-foundry-compares-resident-evil-requiem-on-switch-2-and-xbox-series-s-with-mixed-results)).
- **Budget math:** 0 ms at runtime; it only changes which settings get the budget.
- **Prior art:** [Netflix per-title encoding](https://netflixtechblog.com/per-title-encode-optimization-7e99442b62a2), which spends bits where quality per bit is highest.
- **Tier S.** All games.
- **Cheapest falsification (2 weeks):**
  - Build price-list presets for Wukong and Wilds.
  - At equal measured frame time, compare each against the nearest stock preset: ColorVideoVDP, plus a blind two-choice test on the Deck (at least 30 trials).
  - Kill if the gain is under 0.3 JOD and preference is under 60%.
- **Biggest risk:** settings interact in ways that don't add up, and ColorVideoVDP isn't validated on ghosting.

### 4. Compiler-recipe search with a perfect answer-checker

**Pitch:** Search offline, on a Deck, for the best shader-compiler choices for a game's most expensive pipelines. Ship a few KB of flags per pipeline hash, never shaders.

- **Mechanism:**
  - Rank pipelines by GPU time and take the top 20.
  - Try compiler options that already exist globally:
    - wave32 vs wave64 per stage (`RADV_PERFTEST=cswave32,pswave32,gewave32`);
    - `ACO_DEBUG=nosched-ilp`;
    - register caps to raise occupancy;
    - loop unrolling.
  - Replay a captured frame locally (GFXReconstruct). Require identical output (bit-exact, or within 1 LSB) and time each variant.
  - Apply the winners through a small Mesa patch: driver-config overrides keyed by pipeline hash. Game code never leaves the machine.
- **Why:** a just-in-time compiler tunes for the average shader and has to compile fast. Offline we have unlimited time, the exact chip, and an exact correctness check. Our own AI reverse-engineering assessment found that an automatic checker is what makes automated search work.
- **Budget math:** the top 20 pipelines are about 50–70% of GPU time (est.). Making them 10% faster saves 5–7% of the frame, about 1.6–2.3 ms at 33 ms (est.). No memory cost.
- **Prior art:**
  - GPU vendors' drivers ship per-game shader replacements ([Promit Roy, 2015](https://gamedev.net/forums/topic/666419-what-are-your-opinions-on-dx12vulkanmantle/)).
  - Mesa already ships per-game workarounds in `00-radv-defaults.conf`.
  - vkd3d-proton (Proton's D3D12 layer) already has `VKD3D_SHADER_OVERRIDE` by hash ([README](https://github.com/HansKristian-Work/vkd3d-proton)).
  - [OpenTuner](https://opentuner.org/) (compiler autotuning).
  - A lossy extension, scored with ColorVideoVDP: [genetic shader simplification](https://libraopen.lib.virginia.edu/public_view/jd472w45t).
- **Tier S** (it lives in the driver). All games.
- **Cheapest falsification (2 days):** A/B each option globally on 3 games, then compare pipeline by pipeline in RGP. Kill if no top-20 pipeline moves 8% or more under any option.
- **Biggest risk:** ACO, the shader compiler, may already be near-optimal. A capture of a 10 GB game may not replay within 16 GB.

### 5. A per-game restoration filter trained to that game (the video-codec trick)

**Pitch:** Do what neural post-filters in the VVC video codec do: ship a tiny network trained on *this* game that pulls the Deck's frame toward the High-preset reference.

- **Mechanism:**
  - Offline on a PC, switch between Low and High inside photo mode, which freezes the simulation, to get pixel-aligned image pairs at 1280×800.
  - Train a small convolutional network (300–2,000 multiply-adds per pixel). The loss penalizes flicker between frames and any change to the HUD.
  - Quantize it and run it as a gamescope ReShade effect ([gamescope ReShade](https://gamingonlinux.com/2023/09/gamescope-added-support-for-reshade-shaders-on-linux-steamos)). That happens in the compositor, so nothing loads into the game.
- **Why:** in VVC, tuning the filter to the specific content delivers about half of the post-filter's gain ([Nokia](https://nokia.com/blog/ai-boosts-versatile-video-coding)). A game's content is far more uniform than video, so the systematic Low→High differences (AO darkening, contrast, banding, sharpening) should be learnable.
- **Budget math:**
  - 1.02 Mpx × 1,000 multiply-adds = 1.02 billion per frame.
  - Packed-FP16 peak: 8 CU × 64 lanes × 2 × 2 × 1.6 GHz = 3.28 TFLOPS = 1.64 trillion multiply-adds/s.
  - At 40% efficiency (est.) that's **1.6 ms**; a 300-per-pixel net is about 0.5 ms. Weights are tens of KB.
- **Prior art:**
  - [Cool-chic](https://arxiv.org/abs/2403.11651): a 300-per-pixel decoder beats HEVC, and about 2,000 per pixel matches VVC.
  - Counter-evidence: per-game DLSS 1.0 was replaced by one generic model ([NVIDIA](https://www.nvidia.com/en-us/geforce/news/nvidia-dlss-2-0-a-big-leap-in-ai-rendering/)). That was a whole upscaler, though; this only corrects the remaining difference.
- **Tier S**, anti-cheat games included.
- **Cheapest falsification (2 weeks):**
  - 1,500 pairs from Wukong and Wilds; three model sizes; test on held-out *locations*.
  - Measure ColorVideoVDP on the Deck display model and ms inside gamescope on the Deck.
  - Kill if the gain is under +0.25 JOD at 1 ms or less, or if it vanishes in unseen areas.
- **Biggest risk:** invented or flickering detail, and HUD damage. Training on game frames is legally gray: train locally and ship only the weights.

### 6. Deck-class chips now sell in three markets: get publishers to expose work they already did

**Pitch:** Turn DeckForge's measurements into pressure, through channels that only opened in 2025–26.

- **Facts:**
  - Valve now shows developers the frame-rate distribution of Deck players who opted into telemetry ([Oct 2026](https://www.tweaktown.com/news/113918/valve-introduces-more-steam-deck-framerate-related-telemetry-for-developers/index.html)).
  - Microsoft's [Handheld Compatibility Program](https://news.xbox.com/en-us/?p=213763) warns buyers before purchase when a game isn't handheld-optimized.
  - The base Xbox Ally's Z2 A chip is Deck silicon: 4-core Zen 2, 8 CU RDNA2 ([PCGamesN](https://www.pcgamesn.com/amd/ryzen-z2-a-cpu)).
  - Capcom shipped an RE Engine game on Switch 2 at 540p (see idea 3). Deck-class content paths already exist.
- **Mechanism:** DeckForge would:
  - ask its users to opt into Deck telemetry, so developers' charts show the problem;
  - publish a per-title "handheld gap" scorecard comparing the Deck with that game's Switch 2 and Ally settings;
  - file evidence packets (RGP capture, per-pass timings, Proton log, repro steps) on the vkd3d-proton, Mesa and Proton issue trackers;
  - fund a part-time upstream contractor the way emulators do. Yuzu made about $30k/month from about 7,000 patrons ([overkill.wtf](https://overkill.wtf/nintendo-sue-yuzu-emulator)).
- **Budget math:** 1,000 patrons × $5 = $5k/month, roughly one part-time contractor (est.). One upstream fix reaches every SteamOS user.
- **Tier:** no code in the game; applies to every game.
- **Cheapest falsification (2 weeks to set up):** file 3 evidence packets and send 3 publisher requests. Drop the funding plan if none of the 3 packets gets a maintainer to reproduce it within 30 days.
- **Biggest risk:** publishers fix the Windows/Ally version, not Proton.

---

**What changes in late 2026–27**
- AMD plans FSR 4 for RDNA2, including the Steam Deck, in early 2027 ([mezha](https://mezha.ua/en/news/amd-fsr-4-rdna2-311296/amp/)). Re-run idea 3 when it arrives.
- Driver-side anti-lag ships in Mesa 26.3 (stable in November).
- `VK_EXT_descriptor_heap` is on by default in RADV as of Mesa 26.2 ([Phoronix](https://phoronix.com/news/Mesa-26.2-Released)). Whether vkd3d-proton uses it to cut CPU overhead is still unknown.
- GE-Proton 11-3 integrates OptiScaler ([GamingOnLinux](https://gamingonlinux.com/2026/07/ge-proton-11-3-brings-better-optiscaler-integration-amd-fsr4-improvements-and-lots-of-game-fixes)).
- SteamOS has had the ntsync driver since 3.7.20 ([GamingOnLinux](https://gamingonlinux.com/2026/01/steamos-3-7-20-adds-the-ntsync-driver-to-help-improve-some-game-performance)).

### Unknown unknowns
1. **Our quality metric is set up for a 4K desktop monitor.**
   - FLIP's default is 67 pixels per degree: 0.7 m from a 0.7 m-wide 4K screen (`FLIP.h:118` in [NVlabs/flip](https://github.com/NVlabs/flip)). The Deck at 30 cm is about 42.
   - Run FLIP with `--viewing-conditions 0.30 0.1594 1280`, and tape-measure how far Fede actually holds the Deck. The ranking of settings may flip.
2. **The memory clock.**
   - Log `pp_dpm_mclk` and `pp_dpm_fclk` alongside the GPU clock, at a high sample rate, during the worst 1% of frames.
   - If the memory or fabric clock drops during GPU-bound frames (not checked on the OLED), bandwidth is being wasted, and fixing it is Tier S.
3. **The video encoder as a free motion-vector engine.**
   - Encoder motion vectors can stand in for optical flow at 4× the speed with only minor error ([arXiv 2510.17427](https://arxiv.org/abs/2510.17427)).
   - lsfg-vk computes its motion estimate on the same 8 CUs the game needs.
   - Check whether the Deck's VCN 3 encoder (through its firmware or Mesa's encode path) can hand back motion-vector or statistics buffers.
4. **Does anti-cheat check the driver?**
   - Tier S for ideas 2 and 4 in Space Marine 2 depends on Easy Anti-Cheat not flagging custom Mesa or vkd3d-proton builds.
   - Distros that ship their own Mesa are weak evidence that it's fine. ~~Confirm on a throwaway account before shipping.~~ **[Struck in Round 2: testing anti-cheat on any account is probing; ask the vendor instead (round2/X_anticheat_legal_maint.md).]**
5. **Thread names may label the critical path for free.**
   - Wine may pass `SetThreadDescription` through to Linux thread names (not verified; check `/proc/<pid>/task/*/comm` on the Deck).
   - If it does, Unreal's GameThread, RenderThread and RHIThread can be spotted from outside the process, which is what idea 1 needs.

I wrote no files apart from READMEs downloaded into a scratch folder for fact-checking (`/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/outsider.sM6a`).

**Key facts to keep:**
- SteamOS 3.8 runs kernel 6.16 and supports LAVD.
- AMD plans FSR 4 on the Deck for early 2027.
- The Deck screen is about 42 pixels per degree at 30 cm, while FLIP defaults to 67.
- `RADV_FORCE_VRS_CONFIG_FILE` is Deck-specific and already exists.
