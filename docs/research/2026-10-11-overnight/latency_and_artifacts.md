# Input Latency, Frame Pacing and Visual Artifacts on the Steam Deck (OLED, handheld, SteamOS/gamescope/Proton) — as of 2026-10-11

Conventions used in these notes:
- **[MEASURED]** = an instrumented measurement (LDAT, high-speed camera, timing dump). **[DOC/CODE]** = project documentation or source code (it describes behaviour, it does not measure it). **[CLAIM]** = a vendor, developer or author assertion with no published measurement. **[SUBJECTIVE]** = hands-on impression.
- Every source is dated. Most hard latency measurements found are **not from a Deck**. Deck-specific measured data is thin: two sources (Reddit/Tom's Hardware 2022 and Digital Foundry LDAT via PCGamesN 2023).
- Background compendium skimmed first: `/mnt/user-data/uploads/deckforge-research.md` (2026-09-28). It covers tools and architecture but has no latency data.

---

## 1. The end-to-end latency chain on the Deck (polling → sim → render queue → DXVK/vkd3d swapchain → gamescope → panel), vsync/tearing, limiters, 45@90 vs 40@40

### Takeaway
On the Deck the chain is: input poll, game simulation, CPU-ahead render queue (DXGI default up to 3 queued frames), GPU render, DXVK or vkd3d-proton present, gamescope (direct flip or async-compute composite timed against vblank), then panel scanout. The measured data says two links dominate:
- **The frame limiter you choose.** In 2022 the Steam/gamescope system limiter added roughly 44–90 ms over uncapped, while an in-game limiter added roughly nothing.
- **The refresh rate.** The OLED at 90 Hz measured about 26–33 ms lower than the LCD in Digital Foundry's LDAT tests.

Whether the 2022 limiter penalty still exists on current SteamOS is **unverified**. DeckForge must re-measure it before choosing a limiter strategy.

### Cited Findings
**Measured on the Deck**
- [MEASURED, 2022-05-02] Reddit user Dacvak filmed a Steam Deck LCD at 240 fps ("Is It Snappy?" iOS app). Test: *Rogue Legacy 2* menu, average of 5 runs, stated margin of error ±4 ms. Button-to-photon results:

  | Refresh | Cap | Latency |
  |---|---|---|
  | (default 60 Hz) | Uncapped | 31.8 ms |
  | (default 60 Hz) | Steam 60 fps cap | 75.8 ms |
  | (default 60 Hz) | Steam 30 fps cap | 145.9 ms |
  | 50 Hz | Uncapped | 32.5 ms |
  | 50 Hz | 50 cap | 94.2 ms |
  | 50 Hz | 25 cap | 186.1 ms |
  | 40 Hz | Uncapped | 34.2 ms |
  | 40 Hz | 40 cap | 121.1 ms |
  | 50 Hz (as printed) | 20 cap | 232.0 ms |

  In *Rocket League*, the **in-game** limiter matched to refresh showed "minimal to zero" increase. Source issues: the table prints "400 Hz" for one row, and the text and table disagree on the worst-case row. — [Tom's Hardware](https://www.tomshardware.com/uk/news/steam-deck-framerate-limiter-egregiously-raises-input-latency)
- [CLAIM, 2022-05-04] The same reports say enabling vsync adds about the same latency as the system limiter, and recommend the in-game limiter as the workaround. They also say Switch, PS5 and Xbox come in around 70–80 ms motion-to-photon (no source given for the console figures). — [HotHardware](https://hothardware.com/news/steam-deck-fps-limit-adds-input-latency)
- [MEASURED, Digital Foundry, NVIDIA LDAT; reported by PCGamesN, OLED launch period, Nov 2023]
  - *Crysis 3 Remastered* "90 Hz": LCD 97.7 ms vs OLED 65.2 ms (−32.5 ms, about 33%).
  - *Doom Eternal*: LCD 77.2 ms vs OLED 51.1 ms.
  - At 25 Hz the two models were "neck and neck."
  - The article does not say exactly which refresh or cap each unit ran (the LCD cannot do 90 Hz). — [PCGamesN](https://www.pcgamesn.com/steam-deck/oled-input-lag)

**Swapchain and queue depth (DXVK / vkd3d-proton / DXGI)**
- [DOC] DXGI `SetMaximumFrameLatency`: "The value defaults to 3, but can range from 1 to 16"; it is "the maximum number of back buffer frames that a driver can queue." — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/api/dxgi/nf-dxgi-idxgidevice1-setmaximumframelatency)
- [DOC] DXVK options (dxvk.conf, current master):
  - `dxgi.maxFrameLatency` / `d3d9.maxFrameLatency` (0–16) "Enforce a stricter maximum frame latency. Overrides the application setting."
  - `dxvk.latencySleep` (Auto/True/False): built-in latency reduction. It "assumes that input sampling … happens after the … Present call returns." It "will not have any effect in games with built-in frame rate limiters, or if an external limiter (such as MangoHud) is used," and "may reduce performance or lead to less consistent frame pacing." It uses VK_NV_low_latency2 when the driver exposes it.
  - `dxvk.latencyTolerance` (default 1000 µs).
  - `dxvk.tearFree` (mailbox when vsync is off / relaxed FIFO when it is on).
  - DXVK's own `maxFrameRate` limiter: "DO NOT USE THIS IF EXTERNAL LIMITERS ARE AVAILABLE. Limiters from Mangohud or Gamescope WILL provide a significantly better experience." — [dxvk.conf](https://github.com/doitsujin/dxvk/blob/master/dxvk.conf)
- [DOC] The current vkd3d-proton README documents `VKD3D_SWAPCHAIN_PRESENT_MODE` (IMMEDIATE, MAILBOX, FIFO, FIFO_RELAXED, FIFO_LATEST_READY) and `VKD3D_FRAME_RATE` (built-in limiter). **It does not document `VKD3D_SWAPCHAIN_LATENCY_FRAMES`** (grep of current README). — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/README.md)

**gamescope composition, presentation and limiter**
- [DOC] gamescope README:
  - It receives game frames via Xwayland, "can use DRM/KMS to directly flip game frames to the screen, even when stretching or when notifications are up," and when it must composite, "it does so with async Vulkan compute."
  - ReShade effects "will increase latency" because the work runs on the general gfx+compute queue instead of the async compute queue.
  - `-F fsr` = FSR 1.0 and `-F nis` = NIS (spatial scalers). — [gamescope README](https://github.com/ValveSoftware/gamescope/blob/master/README.md)
- [CODE] gamescope `--framerate-limit`: "Used as a divisor of the refresh rate, rounds down eg 60 / 59 -> 60fps, 60 / 25 -> 30fps." `--immediate-flips`: "Enable immediate flips, may result in tearing." It exports `STEAM_GAMESCOPE_TEARING_SUPPORTED` when the backend supports tearing. — [gamescope src/main.cpp](https://github.com/ValveSoftware/gamescope/blob/master/src/main.cpp)
- [CODE] The gamescope vblank manager wakes the compositor before vblank by a rolling-max "draw time" plus a "red zone":
  - Constants: `kStartingVBlankDrawTime` = 3.0 ms, `kDefaultVBlankDrawTimeMinCompositing` = 2.4 ms, `kDefaultVBlankRedZone` = 1.65 ms, 98% decay.
  - Source inconsistency: a code comment says "0.3ms by default" for the red zone, but the constant is 1,650,000 ns.
  - Comment: "Queueing a flip early is free, the kernel holds it to the panel cycle." — [vblankmanager.hpp](https://github.com/ValveSoftware/gamescope/blob/master/src/vblankmanager.hpp), [vblankmanager.cpp](https://github.com/ValveSoftware/gamescope/blob/master/src/vblankmanager.cpp)
- [CLAIM, 2026-05] The low_latency_layer author describes testing Overwatch 2 "at 4K without Gamescope latency overhead." The author treats gamescope as adding overhead but publishes no figure for it. — [low_latency_layer README](https://github.com/Korthos-Software/low_latency_layer)

**Tearing on the Deck**
- [CLAIM, 2022-10-29] Gaming Mode "always forc[es] VSync." The new "Allow Tearing" option turns vsync off to "reduce any extra latency it introduces." VRR is for external screens only because the internal "screen doesn't support it." — [GamingOnLinux](https://gamingonlinux.com/2022/10/vrr-external-screens-and-allow-tearing-options-coming-to-steam-deck)
- [CLAIM, 2023-01-07] SDHQ says Allow Tearing "is only useful for when outputting to an external monitor or TV." For lowest input lag the author advises setting the SteamOS FPS cap to Off and using in-game vsync. The same page says a cap that matches refresh "will always be better than going to a 1/2 or 1/4 value." — [SDHQ Performance Settings Encyclopedia](https://steamdeckhq.com/tips-and-guides/the-sdhq-performance-settings-encyclopedia/)

### Inferences
- **Chain model for DeckForge, worst to best risk:**
  1. System limiter behaviour (2022 data: +44 ms at 60/60, +87 ms at 40/40 versus uncapped).
  2. Render-queue depth (up to 3 frames ≈ up to 66 ms at 45 fps if the GPU is the bottleneck and nothing throttles the CPU).
  3. Panel refresh period and scanout (11.1 ms at 90 Hz vs 25 ms at 40 Hz).
  4. gamescope composite (roughly 2.4–4.7 ms lead before vblank when compositing; near zero added work on a direct flip).
- **45 fps at 90 Hz vs 40 fps at 40 Hz.**
  - Both are evenly paced: 45 is exactly 90/2, and gamescope's divisor-based limiter lands on it exactly.
  - 45@90 should have lower display-side latency: shorter scanout, and a finished frame can be latched at any 11.1 ms boundary instead of 25 ms. DF's finding that OLED-vs-LCD gaps vanish at 25 Hz but are large at high refresh fits this.
  - 40 fps on a 90 Hz panel is not an integer divisor and would judder unless refresh is set to 40/80.
  - 40@40 is gentler on GPU budget (25 ms frame) but costs display latency.
- **The 2022 Steam-limiter result is the biggest open risk for a "locked 45" product.**
  - If it still holds, DeckForge should prefer the game's own limiter at 45, or a DXVK/vkd3d limiter, or a Reflex-style limiter, over the SteamOS slider. The DXVK docs, however, rate DXVK's limiter as worse than gamescope's/MangoHud's for smoothness, so latency and pacing pull in different directions.
  - This must be measured, not assumed (see section 5).
- **`dxgi.maxFrameLatency = 1`** is the cheapest Tier S lever against queue latency for DX9/10/11 games through DXVK. For DX12 games, the equivalent knob was not found documented in current vkd3d-proton; queue depth is set by the game's own `SetMaximumFrameLatency` and waitable-object usage.

### Gaps
- **Could not find whether Valve fixed the 2022 system-limiter latency.** No release note was found on steamdeck.com (only one page checked, which covered January 2026). No 2023–2026 re-measurement on SteamOS 3.6+/3.7 was found. This is the single most important item to measure on DeckForge's own Deck.
- **`VKD3D_SWAPCHAIN_LATENCY_FRAMES`:** not in the current vkd3d-proton README. Could not confirm whether it still exists, was renamed or was removed. Source-file fetch returned empty.
- **Whether "Allow Tearing" does anything on the OLED's internal panel** (DRM async flips on the internal eDP) is unconfirmed. SDHQ (2023) says external-only; GOL (2022) did not specify.
- **Controller polling rate and input-stack latency** (Steam Input → virtual gamepad) on the Deck: no source found.
- **No published per-stage breakdown** (sim/render/composite/scanout) of Deck latency was found.
- **The DF LDAT article does not state the cap or refresh setting per unit**, so the "90 Hz" comparison is partly ambiguous.

---

## 2. Latency-reduction technology available on Linux/Deck (Anti-Lag 2, VK_NV_low_latency2/Reflex emulation, LatencyFleX, gamescope modes, 2026 developments)

### Takeaway
As of October 2026, the most credible option is **low_latency_layer** (May 2026, MIT). It is an opt-in implicit Vulkan layer that implements both `VK_AMD_anti_lag` and `VK_NV_low_latency2` in a hardware-agnostic way, with dxvk-nvapi forwarding Reflex from games.
- Its author's LDAT data (desktop RX 7900 XTX, not a Deck) shows it matching or beating Windows Anti-Lag 2.
- Mesa's own anti-lag layer (25.3, July 2025) measured as a no-op in those tests.
- LatencyFleX does nothing with vsync on, which is the Deck default.

None of these has been validated on a Deck under gamescope. All are Tier I (injection) under DeckForge's own rules.

### Cited Findings
- [DOC, 2025-07-24] Mesa 25.3 merged `VkLayer_MESA_anti_lag`, an implicit Vulkan layer implementing VK_AMD_anti_lag, written by Valve's Daniel Schürmann. Its algorithm "only tries to minimize the delay between vkQueueSubmit … calls and the start of execution." It is built with `-Dlayers=anti-lag`. CachyOS carried it earlier. No latency numbers. — [Phoronix](https://www.phoronix.com/news/Mesa-Vulkan-AMD-Anti-Lag)
- [CLAIM, 2026-05-17] low_latency_layer developer Nicolas James says Mesa's Anti-Lag 2 implementation "had stability issues and was disabled by default" and reduced latency less than AMD's Windows version. — [Phoronix](https://phoronix.com/news/Low-Latency-Layer)
- [DOC + MEASURED by the developer, 2026] low_latency_layer README:
  - **Enabling it:** opt-in since v0.2.0 via `LOW_LATENCY_LAYER=1`. Add `LOW_LATENCY_LAYER_REFLEX=1` to expose `VK_NV_low_latency2` instead of `VK_AMD_anti_lag`. Suggested Proton launch line: `LOW_LATENCY_LAYER=1 LOW_LATENCY_LAYER_REFLEX=1 DXVK_CONFIG="dxgi.hideAmdGpu = True" %command%`.
  - **FSR 4 conflict:** `PROTON_FORCE_NVAPI=1` and `LOW_LATENCY_LAYER_SPOOF_NVIDIA=1` "are known to break Proton's FSR4 upgrade path."
  - **Test setup:** RX 7900 XTX, 9800X3D, KDE with direct scanout, NVIDIA Reflex Analyzer in an ASUS PG248QP.
  - **Results (relative statements; values are only in chart images):**
    - THE FINALS: matches or beats Windows Anti-Lag 2.
    - CS2: beats Windows.
    - Cyberpunk 2077: Anti-Lag 2 path broken because the app never calls `AntiLagUpdateAMD`; the Reflex path beats Windows AL2.
    - RE Requiem and Overwatch 2: the Reflex path beats Windows Anti-Lag 1, which tracked the Linux baseline.
    - Mesa's anti-lag layer "appears to be a no-op… may even increase latency slightly."
  - **Decoupled sim/render:** Marvel Rivals needs a special delay controller for its decoupled sim/render (`LOW_LATENCY_LAYER_FORCE_DECOUPLED`).
  - **Reflex Boost** is treated the same as On. — [low_latency_layer README](https://github.com/Korthos-Software/low_latency_layer)
- [CLAIM, 2026-05] The Steam Deck is not mentioned in the Phoronix coverage. Intel results are not shown. Performance claims come from the project's own data. — [Phoronix](https://phoronix.com/news/Low-Latency-Layer); see also [GamingOnLinux](https://www.gamingonlinux.com/2026/05/new-low-latency-layer-brings-reflex-and-anti-lag-2-to-amd-and-intel-gpus-on-linux/page=1/)
- [DOC] LatencyFleX README:
  - "does not provide any benefits when VSync is enabled" (blocked on presentation timing).
  - It "introduces jitter in frame time … which results in microstutters."
  - GPU utilization drops to about 95% when GPU-bound.
  - Headline claim: "up to 10ms latency reduction."
  - Anti-cheat warning: direct hooking "can trip the game's integrity check and directly get you banned."
  - Proton path: `PROTON_ENABLE_NVAPI=1 … LFX=1` plus dxvk.conf vendor-ID spoofing. — [LatencyFleX](https://github.com/ishitatsuyuki/LatencyFleX)
- [DOC] DXVK `dxvk.latencySleep=True` provides a built-in, Reflex-free latency limiter for D3D9/D3D11/DXGI games. It has no effect with in-game or external limiters (see section 1). — [dxvk.conf](https://github.com/doitsujin/dxvk/blob/master/dxvk.conf)
- [MEASURED, PCGH 2024-05-02, LDAT, desktop] What Anti-Lag/Reflex buys at the GPU limit:
  - Cyberpunk 4K on RX 7900 XTX, about 76 fps: 67 → 45 ms with Anti-Lag (−22 ms).
  - Starfield on GTX 1080 Ti, about 41 fps: 93 → 72 ms with Reflex (−21 ms). — [PCGH page 2](https://www.pcgameshardware.de/Starfield-Spiel-61756/Specials/Lossless-Scaling-Test-Frame-Generation-FSR-3-DLSS-Latenz-LSFG-1446068/2/)
- [DOC] gamescope: no dedicated "low-latency mode" flag found in `main.cpp` options. Relevant switches are `--immediate-flips` (tearing), `--framerate-limit` and `--adaptive-sync` (VRR, external only on the Deck). — [gamescope src/main.cpp](https://github.com/ValveSoftware/gamescope/blob/master/src/main.cpp)

### Inferences
- **The prize on a GPU-bound Deck at 45 fps is large.** PCGH's desktop data shows a 20+ ms gain from Reflex/Anti-Lag at about 41–76 fps when GPU-bound. The Deck is GPU-bound in exactly the games DeckForge targets, so a Reflex-style limiter at 45 fps is plausibly the largest single latency win available, larger than any present-mode tweak. This needs Deck measurement.
- **Under DeckForge's tier rules, low_latency_layer is Tier I** (an injected Vulkan layer plus GPU-vendor spoofing). It is not for anti-cheat titles, and it conflicts with Proton's FSR 4 upgrade path when the spoof options are used. DeckForge would have to choose per game between the FSR 4 upgrade path and Reflex exposure in some cases.
- **LatencyFleX is likely ineffective on the Deck's internal display** in default Gaming Mode, because gamescope forces vsync there, unless tearing is enabled.
- **For DX11 games without Reflex, `dxvk.latencySleep=True` is the only Tier S option found** (a config file, no injection). It conflicts with using an external limiter for the 45 cap. Whether the gamescope limiter counts as "external" to DXVK must be tested.

### Gaps
- **No Deck/gamescope measurement of low_latency_layer, Mesa anti-lag, LatencyFleX or DXVK latencySleep** was found.
- **low_latency_layer's absolute ms values** are only in chart images, which were not retrieved.
- **Whether SteamOS ships or enables the Mesa anti-lag layer by default** was not found.
- **Whether the `VK_NV_low_latency2` sleep mode includes a built-in frame-rate cap** (a minimum-interval parameter) that could replace the gamescope limiter: not verified this session; check the Khronos spec.
- **No AMD-official Anti-Lag 2 for Linux/RADV** was found beyond the Mesa layer.
- **No 2026 gamescope latency feature** (e.g., present-timing or low-latency scheduling) was found.

---

## 3. Frame generation: latency and artifact costs (lsfg-vk 2x/3x, FSR 3/3.1 FG, FSR 4/Redstone FG via OptiScaler, gamescope/driver FG), minimum base fps

### Takeaway
Interpolation FG always holds back at least one real frame. Measured end-to-end penalties on desktop:
- LSFG: about +26 to +47 ms.
- FSR 3 FG (Starfield, about 41 fps base): about +73 ms, even with Reflex.

That is roughly 1.7–3 base frame times. At a 45 fps base, expect roughly +40–50 ms (inference, not measured on the Deck), taking a heavy game from about 60–90 ms to about 100–140 ms. Every vendor guideline found puts the minimum base at 60 fps (avoid below 30), so **45 fps sits below vendor guidance**. LSFG also cannot separate the HUD from the scene, which causes UI ghosting. **FG cannot meet a "no added latency" bar.** Even with Reflex/Anti-Lag it measured 13–22 ms worse than native *without* reduction, and 35–43 ms worse than native *with* reduction.

### Cited Findings
**Measured latency (PCGH, 2024-05-02, NVIDIA LDAT, 144 Hz monitor, i7-12700K; desktop GPUs)** — [PCGH page 2](https://www.pcgameshardware.de/Starfield-Spiel-61756/Specials/Lossless-Scaling-Test-Frame-Generation-FSR-3-DLSS-Latenz-LSFG-1446068/2/)

| Test | Native | Native + reduction | FG result |
|---|---|---|---|
| Starfield, GTX 1080 Ti, about 41 fps base (closest analogue to a 45 fps Deck base) | 93 ms | 72 ms (Reflex) | LSFG + Reflex 115 ms; LSFG 140 ms; **FSR 3 FG + Reflex 145 ms**; FSR 3 FG 150 ms; LSFG + FSR 3 FG + Reflex 231 ms |
| Cyberpunk 4K, RX 7900 XTX, about 76 fps base | 67 ms | 45 ms (Anti-Lag) | LSFG + AL 80 ms; LSFG 107 ms; AFMF + AL 76–77 ms |
| Cyberpunk, RTX 4080 Super, about 62 fps base | 39 ms | 39 ms (Reflex) | DLSS 3 FG 61 ms; LSFG + Reflex 90 ms; LSFG 103 ms |
| CS2, 65 fps cap, 7900 XTX | 22 ms | — | LSFG 48 ms; AFMF 51 ms |
| CS2, 65 fps cap, 4080S | 25 ms | — | LSFG 41 ms |

PCGH's conclusions:
- FG "roughly doubles latency" at a 65 fps cap.
- With a controller the differences are "less noticeable" [CLAIM].
- LSFG "doesn't separate game content from the UI," so it produces more artifacts than FSR 3, and its blur can cause motion sickness.

**Vendor and author guidance on base fps**
- [CLAIM/guidance, PCGH page 1, 2024-05-02] Cap the game at half the monitor refresh. Ideally have "mindestens 60 Fps" before LSFG. Frame-pacing problems become likely below 30 fps. LSFG intermediate frames show "starke Artefakte" (strong artifacts) and "Instabilitäten" (instabilities). In the Kingdom Come comparison, LSFG ran with about 10% fewer natively rendered fps. — [PCGH page 1](https://www.pcgameshardware.de/Starfield-Spiel-61756/Specials/Lossless-Scaling-Test-Frame-Generation-FSR-3-DLSS-Latenz-LSFG-1446068/)
- [DOC, AMD GPUOpen, FSR 3.1.5 page, SDK 2.0, Aug 2025]
  - FSR 3 FG "runs best when interpolating from a minimum of 60 fps." Below 60, interpolation artifacts become more visible; avoid below 30 fps.
  - VRR-off + V-Sync-on limits output to integer divisors of refresh and "can cause judder."
  - UI composition is a required integration step (three options are listed).
  - FSR 3.1.1 added Anti-Lag 2 support. — [GPUOpen FSR 3](https://gpuopen.com/fidelityfx-super-resolution-3/)
- [SUBJECTIVE, TechPowerUp, Forspoken FSR 3 review]
  - 30 fps base → 60 with FG felt like "around 35 FPS" latency, "very slow and sluggish."
  - 70 → 140 felt like about 80 fps.
  - Artifacts: disocclusion around the character, shimmering and temporal instability, and aliased particles, all amplified in generated frames. Frame-pacing stutter without vsync plus a cap. No UI issues with FSR 3 FG.
  - AMD's recommendation is quoted as ≥60 fps (AFMF ≥70).
  - Page date shows 2024-04-28 (may be a render date). — [TechPowerUp](https://www.techpowerup.com/review/forspoken-fsr-3/)
- [CLAIM, aggregator, updated 2026-10-04] Intel recommends a 60 fps base for XeSS 3 MFG (cites PC Guide 2026-02-18). The page's own latency numbers are arithmetic (1000/base fps), not measurements. — [FPSHQ](https://fpshq.com/en/wiki/frame-generation-latency/)

**lsfg-vk on the Deck (2026 state)**
- [DOC] The Decky LSFG-VK plugin exposes:
  - FPS multiplier 2x/3x/4x.
  - "Flow Scale" ("lower = better performance, higher = better quality").
  - "Performance Mode" (a lighter model, "recommended for most games").

  It requires the paid Lossless Scaling app (its "lsfg-vk" beta branch). — [decky-lsfg-vk README](https://github.com/xXJSONDeruloXx/decky-lsfg-vk)
- [SUBJECTIVE, SDHQ 2026-08-07, experimental lsfg-vk 2.0 plugin vs Decky-lsfg on a Deck]
  - Ghosting reduced "in some cases" (a bug fix already in the 1.0 dev build).
  - "does not improve image quality"; "no frame-pacing improvements."
  - "Input lag may be slightly better, but I could still feel a delay."
  - On build 24: 2x stuttered in Iron Nest, 3x showed "graphical artifacting," adaptive FG "felt awful."
  - PancakeTAS (lsfg-vk author) said some GitHub claims about the experimental build were fabricated. — [SDHQ](https://steamdeckhq.com/news/lossless-scaling-2-0-doesnt-improve-frame-gen/)
- [CLAIM, SDHQ 2026-09-06] lsfg-vk 2.0.0 (released about 2026-09-05):
  - FP16 acceleration "2x to 3x" performance (author saw improvement, no figures).
  - About 70% less memory; Vulkan 1.2 minimum; 32-bit game support; Qt6 UI; per-game profiles; a benchmark/validation tool.
  - No latency or pacing changes mentioned. The author "still notices input lag," and a low base fps "still causes drops and stutters."
  - The Decky plugin had not yet updated. The MAKO plugin, the only Decky route at the time, is not recommended (AI-generated code). — [SDHQ](https://steamdeckhq.com/lsfg-vk-lossless-scaling-huge-2-0-0-release/)
- [CLAIM, ETA Prime via Notebookcheck, 2025-01-15, ROG Ally X] LSFG 3 gave about 44→74 fps (Hogwarts) and about 30→60 (Starfield). Latency was "workable," with no ms values. — [Notebookcheck](https://www.notebookcheck.net/Lossless-Scaling-3-shown-to-deliver-up-to-3x-FPS-boost-on-last-gen-gaming-handheld-with-workable-frame-latency.947697.0.html)

### Inferences
- **Translating PCGH's numbers into base frame times:**
  - Starfield (24.4 ms base): LSFG ≈ +1.8–1.9 frames, FSR 3 FG ≈ +3 frames.
  - Cyberpunk (13.2 ms base): LSFG ≈ +2.7–3.0 frames.
  - CS2 (15.4 ms base): ≈ +1.0–1.7 frames.
  - Applied to a 22.2 ms (45 fps) Deck base: **LSFG ≈ +22–65 ms, central estimate about +40–45 ms.**
  - On a Deck the FG pass itself also costs GPU time on an already-saturated 8-CU GPU. PCGH saw about 10% fewer base fps even on a 1080 Ti. If FG drags the base below 45, the penalty grows and pacing breaks.
- **"45 → 90 with FG" delivers 90 Hz motion with latency at or worse than native 30 fps.** That is consistent with TechPowerUp's "30→60 feels like 35 fps." Under the owner's "no added latency" rule, FG at a 45 base fails by construction. It can only be offered as an explicitly labelled opt-in, which matches the CLAUDE.md rule that FG never counts toward the native target.
- **Best-case FG on the Deck pairs FG with a Reflex-style limiter.** That means low_latency_layer plus Reflex in games that support it, and in-engine FSR 3.1 FG or OptiScaler FG rather than LSFG, since in-engine FG gets motion vectors and UI separation. PCGH data still put "FG + reduction" above "native without reduction."
- **Artifacts scale with base frame time.** A larger gap between real frames (22 ms at 45 vs 16.7 ms at 60) means larger motion between frames and more disocclusion. AMD explicitly ties visible artifacts to sub-60 bases. HUD ghosting is structural for LSFG (no UI mask) and will appear in every game with a HUD.

### Gaps
- **No Deck-measured FG latency** (LDAT or camera) was found for lsfg-vk, FSR 3.1 FG or OptiScaler FG at 30–45 fps base.
- **No source found for FSR 4 / "Redstone" ML frame generation running on RDNA 2/INT8**, nor for its latency/artifact profile. **No gamescope- or driver-level FG** for the Deck was found as of Oct 2026.
- **The 3x mode at a 30 fps base:** no measurements, only SDHQ's "graphical artifacting" impression.
- **The lsfg-vk upstream wiki/README** (PancakeTAS) could not be retrieved (404 on raw paths). Its documented recommended base fps and present-mode options remain unverified.

---

## 4. Upscaler artifacts at Deck resolutions (FSR 1/2/3.1, FSR 4 INT8, XeSS DP4a, TSR, LS1; 540–720p → 800p)

### Takeaway
Evidence quality here is weak: almost no Deck-resolution artifact studies exist.
- **What exists:** FSR 2/3-class upscalers show shimmering, disocclusion and particle aliasing that worsen at low output resolutions. FSR 4 (INT8 via OptiScaler) looks markedly cleaner on the Deck per Deck Wizzard's comparisons. AMD is bringing FSR 4.1 INT8 to RDNA 2 officially in early 2027 (Deck support unconfirmed).
- **The critical new number:** FSR 4 INT8 costs 3.9–7.1 ms at 1080p output on a 24-CU RDNA 2 BC-250. Scaled to the 8-CU Deck at 800p, that suggests roughly 6–11 ms, i.e. **about 25–50% of the 22.2 ms budget** (inference).

### Cited Findings
- [DOC, AMD GPUOpen] FSR scale factors:

  | Mode | Scale | Input at 1080p output |
  |---|---|---|
  | Native AA | 1.0x | 1920×1080 |
  | Quality | 1.5x | 1280×720 |
  | Balanced | 1.7x | about 1129×635 |
  | Performance | 2.0x | 960×540 |
  | Ultra Performance | 3.0x | 640×360 |

  AMD now recommends "FSR Upscaling" (formerly FSR 4) for new integrations. — [GPUOpen FSR 3](https://gpuopen.com/fidelityfx-super-resolution-3/)
- [SUBJECTIVE, TechPowerUp, Forspoken FSR 3] Shimmering/temporal instability, disocclusion artifacts around the main character, and "blurry, pixelated, aliased particle effects, especially at 1080p and 1440p." — [TechPowerUp](https://www.techpowerup.com/review/forspoken-fsr-3/)
- [SUBJECTIVE, Deck Wizzard via PCGH, 2025-09-20] FSR 4 (INT8 via OptiScaler) on the Steam Deck/OLED:
  - Quality improves "dramatically" over FSR 3.1.5 in FF7 Rebirth and Stellar Blade.
  - Cleaner and sharper with better distant detail in Cyberpunk and Spider-Man 2.
  - The performance loss vs FSR 3.1.5 is "comparatively small," and better quality allows a more aggressive preset.
  - No ms figures. — [PCGH](https://www.pcgameshardware.de/FidelityFX-Super-Resolution-Software-277617/News/FSR-4-auf-dem-Steam-Deck-1482538/)
- [CLAIM, TechSpot, 2026-05-14] AMD (Jack Huynh) announced:
  - FSR 4.1 for RX 7000 "this summer" and RX 6000 (RDNA 2) "early 2027."
  - Older cards use INT8, "a slower alternative" to FP8.
  - INT8 quality is "close enough to the FP8 version … that most users will struggle to tell the difference."
  - TechSpot found FSR 4 slower than FSR 3 but faster than native.
  - Handheld/Steam Deck support is not confirmed in the body text. — [TechSpot](https://www.techspot.com/news/112412-fsr-4-upscaling-finally-coming-older-radeon-gpus.html)
- [CLAIM, SDHQ 2026-05-14] "FSR 4 … does hurt performance" on the Deck. Current route: OptiScaler injection. A reader reports OptiScaler "never really runs" with RE Engine games on the Deck. **Conflict:** SDHQ states FSR 4 uses FP8, not INT8. That contradicts TechSpot and the RDNA 2 hardware fact (no FP8; see compendium), so SDHQ is likely wrong on this point. — [SDHQ](https://steamdeckhq.com/?p=50571)
- [MEASURED, community fork, Guru3D 2026-09-14] FSR 4 INT8 median dispatch time on a BC-250 (RDNA 2, 24 CUs stock, up to 40 with community firmware; CU count used not stated), Linux/Mesa/GE-Proton, before → after the "BC-250 FSR 4 fork" 4.0.0-rc9:

  | Output | Before | After |
  |---|---|---|
  | 1080p | 7.13 ms | 3.93 ms |
  | 1440p (from 1706×960) | 11.51 ms | 5.92 ms |
  | 4K | 25.72 ms | 12.08 ms |

  Applicability to other RDNA 2 parts is "unqualified." — [Guru3D](https://www.guru3d.com/story/optimized-fsr-4-nearly-halves-upscaling-time-on-amd-repurposed-bc250-mining-board/)
- [DOC] gamescope's built-in scalers are spatial FSR 1.0 and NIS (no temporal data, so no ghosting, but no reconstruction either). — [gamescope README](https://github.com/ValveSoftware/gamescope/blob/master/README.md)
- [CLAIM, SDHQ 2023] The SteamOS scaling filters are Linear, Nearest, Integer and FSR. "Half-Rate Shading" applies VRS that "will half the shading quality." — [SDHQ Encyclopedia](https://steamdeckhq.com/tips-and-guides/the-sdhq-performance-settings-encyclopedia/)

### Inferences
- **At 1280×800 output, FSR Quality renders about 853×533 and Performance about 640×400** (arithmetic from AMD's scale factors). That is below the 720p/540p inputs where desktop reviewers already report shimmer and disocclusion. Temporal upscalers have very few input pixels on the Deck, so ghosting and shimmer risk is at its highest.
- **FSR 4 INT8 cost estimate on the Deck (rough):**
  - Scale the BC-250 1080p numbers by output pixels (800p ≈ 0.49× of 1080p) and by CU count (8 vs 24, ≈3×).
  - Result: roughly **5.8 ms (optimized rc9) to 10.6 ms (pre-optimization)** on the Deck, before accounting for its lower clocks and much lower LPDDR5 bandwidth (88 GB/s per compendium), which would push it higher.
  - Against a 22.2 ms budget, FSR 4 may consume a quarter to half the frame.
  - **This is the main trade-off for the "native look" goal:** FSR 4's artifact reduction comes at a big GPU cost that forces a lower input resolution or other cuts. It must be measured per game on the Deck.
- **Spatial scalers trade one artifact for another.** FSR 1 / NIS (gamescope) and LS1 have no temporal artifacts (no ghosting or disocclusion trails), but they cannot remove aliasing and shimmer that the game's own AA leaves. For a "no ghosting" policy they are the safe choice. For a "no shimmer" policy they are not.

### Gaps
- **No Deck-resolution comparison was found** (or retrieved) for XeSS DP4a vs TSR vs FSR 2/3.1 vs FSR 4 (ghosting, shimmer, disocclusion). The searches surfaced only forum threads.
- **No source on Lossless Scaling's LS1 spatial upscaler quality.**
- **No measured FSR 4 INT8 ms cost on an actual Steam Deck**, and no FSR 3.1 or XeSS DP4a ms cost on the Deck.
- **Whether official FSR 4.1 INT8 (early 2027) will include RDNA 2 APUs such as Van Gogh**: unconfirmed.

---

## 5. Measuring latency and artifacts without special hardware

### Takeaway
A 240 fps phone camera plus averaging is a proven Deck method: the 2022 limiter study reported ±4 ms. It is good enough to rank configurations that differ by 10+ ms, which covers every effect in sections 1–3. On-device software can log frame pacing (MangoHud frame times) but not end-to-end latency. For artifacts, full-reference temporal metrics now exist:
- ColorVideoVDP (spatio-temporal).
- Intel's CGVQM (2025), calibrated specifically on neural supersampling, frame interpolation and VRS distortions.

FLIP is image-only. All three need a reference capture of the same frames, so deterministic replay or a fixed camera path is a prerequisite.

### Cited Findings
- [MEASURED method, 2022] Dacvak's method: iPhone 240 fps capture with the "Is It Snappy?" app. Count frames from full button press to the first screen change. Five runs averaged per setting. Stated margin about ±4 ms. — [Tom's Hardware](https://www.tomshardware.com/uk/news/steam-deck-framerate-limiter-egregiously-raises-input-latency), [HotHardware](https://hothardware.com/news/steam-deck-fps-limit-adds-input-latency)
- [MEASURED method] Professional reference: NVIDIA LDAT, used by Digital Foundry on the Deck and by PCGH (about 120–350 runs per configuration). — [PCGamesN](https://www.pcgamesn.com/steam-deck/oled-input-lag), [PCGH page 2](https://www.pcgameshardware.de/Starfield-Spiel-61756/Specials/Lossless-Scaling-Test-Frame-Generation-FSR-3-DLSS-Latenz-LSFG-1446068/2/)
- [DOC] The DXVK HUD exposes a `frametimes` graph. No latency HUD element was found in the README. — [DXVK README](https://github.com/doitsujin/dxvk/blob/master/README.md)
- [DOC] The Vulkan `VK_NV_low_latency2` extension includes `vkGetLatencyTimingsNV` (per-frame latency timing query). Its existence was confirmed via Khronos refpage search results; contents not reviewed. — [Khronos refpage](https://docs.vulkan.org/refpages/latest/refpages/source/vkGetLatencyTimingsNV.html)
- [DOC] NVIDIA FLIP compares a test image against a reference image (`flip -r reference.png -t test.png`), under a BSD-3 license. It is image-pair based. — [NVlabs/flip](https://github.com/NVlabs/flip)
- [DOC] ColorVideoVDP is "a full-reference visual quality metric" for images and videos. It is "the first color-aware metric that accounts for spatial and temporal aspects of vision" and "predict[s] visibility of … temporally varying artifacts." PyTorch, CUDA or CPU (CPU much slower for video). Paper: doi:10.1145/3658144 (2024). — [ColorVideoVDP](https://github.com/gfxdisp/ColorVideoVDP)
- [DOC/CLAIM, Intel, 2025-06-13] CGVQM+D is a full-reference video quality metric with per-pixel error maps and global scores.
  - **Dataset distortions:** neural supersampling, novel-view synthesis, path tracing, neural denoising, frame interpolation and VRS.
  - **Benchmark claim:** existing full-reference metrics reach at most Pearson 0.78 on this dataset, and CGVQM "significantly outperforms" them.
  - Code and dataset are on GitHub. — [Intel](https://www.intel.com/content/www/us/en/developer/articles/technical/cgvqm-d-computer-graphics-video-quality.html), [IntelLabs/CGVQM](https://github.com/IntelLabs/CGVQM), [arXiv 2506.11546](https://arxiv.org/abs/2506.11546)
- [DOC, internal] The compendium already plans MangoHud CSV frame-time logs, GFXReconstruct deterministic replay, and FLIP/SSIM scoring against a high-quality reference. — `/mnt/user-data/uploads/deckforge-research.md` (sections 3.5, 4, 6)

### Inferences
- **A practical DeckForge latency protocol (no special hardware):**
  - Mount a phone at 240 fps to see both a physical input (e.g., the A button, or a stick flick that moves the camera) and the screen.
  - Use a repeatable in-game action with an instant visual response.
  - Take ≥10–20 trials per configuration. A 240 fps camera quantizes at 4.17 ms, so averaging is mandatory.
  - Report the median and IQR.
  - Always include a baseline (uncapped, in-game limiter) in the same session.
  - This is enough to settle the open questions: Steam limiter vs in-game limiter at 45, `maxFrameLatency=1`, low_latency_layer, and FG on/off.
- **Software-only estimates.** A DeckForge read-only Vulkan layer could timestamp `vkQueuePresentKHR` and GPU completion to estimate queue depth and render latency. If a Reflex path is active, `vkGetLatencyTimingsNV` may provide per-stage timestamps. Neither captures input-stack or panel latency, so they complement the camera; they don't replace it.
- **Artifact scoring.** Use ColorVideoVDP or CGVQM (temporal) as the gate for upscaler and FG choices, and FLIP only for still-frame triage.
  - For FG, the natural reference is the same replay rendered natively at 90 fps; for upscalers, native 800p or supersampled frames.
  - Captures must be lossless and frame-exact, which favours GFXReconstruct replay plus an offscreen capture, not phone video.
  - These metrics run on a PC (CUDA), not on the Deck.

### Gaps
- **No PresentMon-equivalent for Linux/gamescope** (one that reports per-frame "PC latency") was found. MangoHud's latency capabilities were not re-verified this session.
- **No validated low-cost photodiode/Arduino setup for the Deck** (OSLTT-style) was found. The Deck's built-in controller makes automated input injection non-trivial.
- **CGVQM's licence** was not read (a badge only), and its compute cost per clip was not found.
- **No published thresholds were found that map ColorVideoVDP/CGVQM scores to "visible to a typical player on a 7-inch 800p screen."**

---

## 6. Evidence-backed "native feel" thresholds (latency at 45 fps native vs 90 fps FG)

### Takeaway
No study found sets a just-noticeable-difference (JND) for added latency in controller-driven handheld play. What the evidence supports:
- **Measured Deck baselines:** about 51–65 ms for real games on the OLED at high refresh (DF/LDAT). About 32 ms for a trivial 2D menu. Consoles are about 70–80 ms per a 2022 claim.
- **Latency matters more than refresh rate** for targeting once above 60 Hz (NVIDIA, 2019).
- **FG at about 40–45 fps base adds roughly 40–75 ms** measured on desktop, more than the entire OLED baseline.

A defensible DeckForge rule: "native feel" means ≤ the latency of the same game at native 45 fps with the best non-FG settings, within camera noise (±5 ms). Interpolation FG at a 45 base cannot meet that rule.

### Cited Findings
- [MEASURED, NVIDIA Research, SIGGRAPH Asia 2019] Spjut et al., "Latency of 30 ms Benefits First Person Targeting Tasks More Than Refresh Rate Above 60 Hz." Eight skilled esports athletes. Reduced latency clearly shortened task completion time. Refresh rate had "relatively minor effects" once its latency benefit was removed, with a small, marginally significant benefit only for some tracking tasks. — [NVIDIA Research](https://research.nvidia.com/publication/2019-11_Latency-of-30)
- [MEASURED, DF via PCGamesN] Steam Deck OLED: Doom Eternal 51.1 ms, Crysis 3 Remastered 65.2 ms (LCD 77.2 / 97.7 ms). — [PCGamesN](https://www.pcgamesn.com/steam-deck/oled-input-lag)
- [MEASURED, 2022] Steam Deck LCD, light 2D game: about 32–34 ms uncapped. 76 ms at a system 60 cap, 121 ms at 40 Hz/40 cap. — [Tom's Hardware](https://www.tomshardware.com/uk/news/steam-deck-framerate-limiter-egregiously-raises-input-latency)
- [CLAIM, 2022] Switch/PS5/Xbox about 70–80 ms motion-to-photon (unsourced in the article). — [HotHardware](https://hothardware.com/news/steam-deck-fps-limit-adds-input-latency)
- [MEASURED, PCGH 2024] FG at about 41 fps base: native + Reflex 72 ms vs LSFG + Reflex 115 ms vs FSR 3 FG + Reflex 145 ms. Controller users notice differences less than mouse users [CLAIM]. — [PCGH page 2](https://www.pcgameshardware.de/Starfield-Spiel-61756/Specials/Lossless-Scaling-Test-Frame-Generation-FSR-3-DLSS-Latenz-LSFG-1446068/2/)
- [SUBJECTIVE, TechPowerUp] 30→60 FG "feels" like about 35 fps; 70→140 like about 80 fps. — [TechPowerUp](https://www.techpowerup.com/review/forspoken-fsr-3/)
- [DOC] AMD: FG best at a ≥60 fps base, avoid below 30. — [GPUOpen](https://gpuopen.com/fidelityfx-super-resolution-3/)
- [Bibliographic only] Raaen & Eg (2015), "Instantaneous human-computer interactions: Button causes and screen effects," HCI International 2015. This is the button-to-screen latency detection study, but its numbers could not be retrieved. — [Simula](https://www.simula.no/publications/instantaneous-human-computer-interactions-button-causes-and-screen-effects)

### Inferences
- **Approximate budget at native 45 fps on the OLED** (inference from the above):
  - Frame time 22.2 ms.
  - A GPU-bound queue of 1–3 frames adds 0–44 ms beyond one frame.
  - Display 90 Hz scanout plus vsync latch: about 6–17 ms.
  - Input plus sim: unknown.
  - Expected total: roughly 55–90 ms. That is consistent with DF's 51–65 ms for games running above 45 fps.
  - Reflex-style queue control could pull a GPU-bound 45 fps game toward the low end. PCGH saw about −21 ms at about 41 fps on desktop.
- **The same game at 45 → 90 FG** is likely about 100–140 ms without reduction, or about 95–115 ms with Reflex (scaling PCGH's Starfield deltas). That is roughly native-30-fps-class responsiveness or worse, with 90 Hz motion clarity.
- **Proposed thresholds for DeckForge, written as testable acceptance criteria. These are a judgement built on the evidence above, not established perceptual constants:**
  - **(a)** "Native feel" latency = median camera-measured latency ≤ native-45 best-config + 5 ms (the camera noise floor).
  - **(b)** Any configuration adding ≥ about 20 ms is "not native." That is about one 45 fps frame, and roughly the size of the Reflex/Anti-Lag effect that reviewers describe as clearly noticeable.
  - **(c)** FG is reported separately with its measured delta, never folded into the native verdict.
  - **(d)** Base fps < 30 is never acceptable for FG (AMD, PCGH).
- **Controller use (thumbstick camera, not mouse flicks) probably raises the tolerable threshold** (PCGH claim, DF's "neck and neck" at low refresh). No controlled study was found to quantify it, so DeckForge should not loosen thresholds on that basis without its own blind tests.

### Gaps
- **No peer-reviewed JND for added latency with a gamepad on a handheld** was found. Raaen & Eg 2015 and the Blur Busters "Human Reflex" material were located but not read. Their numbers should be retrieved before the report quotes any JND.
- **No study was found on perceptibility of FG artifacts** (UI ghosting, disocclusion) at 7-inch, 800p viewing distance, or on how low a base fps players accept FG at on handhelds.
- **No measured end-to-end latency for a demanding game on the Deck OLED at exactly a locked 45 fps / 90 Hz** (with each limiter type) was found. DeckForge's first measurement experiment should produce it.
