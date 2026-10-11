# Upscaling and image reconstruction on the Steam Deck OLED (RDNA2, INT8/DP4a, no FP8), as of October 2026

Researched 2026-10-11. Tags used below: **[MEASURED]** = numbers someone captured on hardware; **[CLAIM]** = vendor/author statement without data; **[ADVICE]** = a recommendation; **[DOC]** = primary documentation or source code. Frame budget reference: 45 fps = 22.2 ms. 1280x800 output internal resolutions at standard ratios: Native AA 1280x800; Quality 1.5x = 853x533; Balanced 1.7x = 753x471; Performance 2.0x = 640x400; Ultra Performance 3.0x = 427x267 (ratios from [AMD FSR2 README](https://github.com/GPUOpen-Effects/FidelityFX-FSR2)).

Compared with the 2026-09-28 compendium, which only said "FSR 4 runs via the INT8 path at a real cost", these notes add new information on: AMD's official RDNA2 date (early 2027) and a separate "lighter" handheld model; FSR 4.1.1 INT8 already running on RDNA2/Deck through Proton-CachyOS, OptiScaler 0.9.4 and Decky Framegen pre-releases; the first per-frame ms figures at 800p on the Deck; a community fork that halves FSR 4 cost on RDNA2 silicon (BC-250); the HelixSR DLSS-CNN-on-compute-shaders mod (Oct 2026); and exact LOD-bias and sharpening knobs in dxvk, OptiScaler and gamescope.

---

## Q1. FSR 4 / 4.1 on RDNA2 and the Steam Deck: official status, Proton status, measured cost, quality vs FSR 3.1

### Takeaway
AMD has **not** officially shipped FSR 4 for RDNA2. Its stated RDNA2 date is "early 2027", and it has promised a separate "lighter" FSR 4 for handheld/APU GPUs by the end of 2026, without naming the Deck. FSR 4.1.1 INT8 **already runs on the Deck unofficially** (Proton-CachyOS, OptiScaler 0.9.4 with `Fsr4ForceEnableInt8`, Decky Framegen pre-releases). The best Deck figure is about **4.5 ms per frame at 800p output**, roughly 20% of a 45 fps budget, against an estimated 1–2 ms for FSR 3.1. Every source that compared them found the quality clearly better than FSR 3.1, especially for shimmer and distant detail.

### Cited Findings
**Official AMD status**
- [CLAIM] 2026-05-14: AMD's Jack Huynh (SVP/GM Computing & Graphics) posted on X that RDNA 3 gets "FSR Upscaling 4.1" in July 2026, in 300+ games at launch, and that **RDNA 2 support comes in "early 2027"**. No performance numbers were given, and the INT8 path was not mentioned. — [GamingOnLinux, 2026-05-14](https://www.gamingonlinux.com/2026/05/amd-announce-fsr-upscaling-4-1-officially-coming-to-rdna-3-and-rdna-2/)
- [CLAIM] 2026-10-07/08: Huynh told Korean media (via The Elec) that FSR 4 "will be supported on laptops, APUs, and handheld devices by the end of 2026". He described a "lighter model" / "special lightweight version" for integrated graphics, and even named the Ryzen Z2 Extreme and Ryzen AI Halo as too weak for standard FSR 4. **The Steam Deck is not named.** SDHQ only *speculates* that the Deck gets official support "next year", on the RDNA2 timeline. — [Steam Deck HQ, 2026-10-08](https://steamdeckhq.com/news/amd-fsr-4-confirmed-for-handhelds-2026/); [Notebookcheck, 2026-10-07](https://www.notebookcheck.net/FSR-4-special-version-to-boost-gaming-performance-on-handhelds-coming-this-year.1418417.0.html)
- [CLAIM, weak] NoobFeed's headline "AMD FSR 4.1 Confirmed for Steam Machine and Steam Deck" (2026-05-15) cites no Valve or AMD statement that names the Deck. Treat it as unverified. — [NoobFeed, 2026-05-15](https://www.noobfeed.com/hardware/amd-fsr-4-1-steam-machine-steam-deck)
- [MEASURED, RDNA3 desktop] Official FSR 4.1 INT8 on an RX 7900 XTX (driver 26.6.2) costs about 11% performance vs FSR 3.1 in Quality mode and up to 14% in Performance mode. ComputerBase 4K averages: FSR 4.1 Quality +40% vs FSR 3.1 Quality +57% over native; Performance +73% vs +103%. Community tests put RDNA2 overhead at "10–20%". — [igor'sLAB summarising ComputerBase/TechSpot, 2026-07-08](https://www.igorslab.de/en/fsr-4-1-rdna-3-better-image-quality-rx-7900-xtx-up-to-14-percent-performance/)

**Proton / Linux status (the Deck's actual path)**
- [DOC] Proton-EM docs: `PROTON_FSR4_UPGRADE=1` auto-downloads the FSR 4.0.0 DLL (Proton-EM 10.0-22+). RDNA3 needs `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`. "**RDNA2 and RDNA1 require [doitsujin's coopmat-layer] Vulkan layer. Keep your expectations low because the performance will be pretty terrible.**" Watermark check: `FSR4_WATERMARK=1`. The doc is undated and predates 4.1.1 INT8. — [Proton-EM FSR4.md](https://github.com/Etaash-mathamsetty/Proton/blob/em-10-hdrtest/docs/FSR4.md)
- [DOC/news] vkd3d-proton 3.0 (2025-11-19) implemented FSR 4 on Vulkan cooperative-matrix and float8 shader extensions. An **emulation fallback using INT8 + FP16** lets RDNA2/RDNA3 run it. The fallback is **off by default** and "carries a measurable performance penalty". — [Guru3D, 2025-11-19](https://www.guru3d.com/story/vkd3dproton-30-adds-amd-fsr4-antilag-supports-older-rdna-gpus/)
- [News] 2026-06-27: an FSR 4.1.1 INT8 `amdxcffx64.dll` briefly appeared in the **Proton Experimental depot**, and the manifest was then removed. Reported results: works on RDNA3/3.5, "partial function with artifacts" on RDNA2 (Wccftech). PC Gamer reports Valve is working with AMD on FSR 4 for the Steam Machine. — [igor'sLAB, 2026-06-27](https://www.igorslab.de/en/valve-fsr-4-1-proton-experimental-rdna-3-3-5/)
- [DOC/news] Proton-CachyOS 11.0-20260702 imported Proton-EM's `amdxc64` changes to enable **FSR 4.1.1 "on all supported hardware"**. `amdxcffx64.dll` is now copied automatically. `PROTON_FSR4_UPGRADE` now only pins a version (4.0.0 or 4.1.1; more with OptiScaler). A new `FSR4_UPGRADE` var upgrades FSR3/4 to FSR4 (FP8 or I8) using "the 4.1.1 DLL from Proton Experimental" and is "not needed on RDNA2-4 discrete GPUs". `MLFG_UPGRADE` enables Redstone ML frame gen. `PROTON_FSR4_RDNA3_UPGRADE` was removed, and `PROTON_FSR3_UPGRADE` was renamed `PROTON_FFX3_UPGRADE`. — [GamingOnLinux, 2026-07-13](https://www.gamingonlinux.com/2026/07/proton-cachyos-version-11-0-20260702-brings-amd-fsr4-upgrades-pipewire-changes/)
  - [Reader comment, not article] "`FSR4_UPGRADE=1` on integrated GPUs costs about 25% performance; only worth it if base framerate is ~60+." — same page
- [MEASURED, desktop RDNA2] With proton-cachyos-11.0, games with FSR 3.1+ were switched to FSR 4.1.1 automatically on an RX 6700 XT. Results were "stable" in Resident Evil Requiem and Marvel Rivals, with no fps given. — [GameGPU, 2026-07-13](https://en.gamegpu.com/news/zhelezo/rdna-2-poluchila-podderzhku-fsr-4-1-na-operatsionnoj-sisteme-linux-ranshe-windows)
- Conflict: one source says Valve removed the Proton Experimental manifest ([igor'sLAB](https://www.igorslab.de/en/valve-fsr-4-1-proton-experimental-rdna-3-3-5/)), while Proton-CachyOS sources its 4.1.1 DLL "from Proton Experimental" ([GOL](https://www.gamingonlinux.com/2026/07/proton-cachyos-version-11-0-20260702-brings-amd-fsr4-upgrades-pipewire-changes/)). The DLL is evidently obtainable either way. I found no Valve changelog announcing an FSR4 RDNA2 path in **stock** Proton.

**Steam Deck measurements (the core numbers)**
- [MEASURED, community] **Steam Deck at 1400 MHz GPU: FSR 4 ≈ 4.5 ms/frame at 800p and ≈ 11 ms at 1080p. HelixSR (DLSS 3.7 CNN) ≈ 3.5 ms at 800p and ≈ 7 ms at 1080p.** This is a ResetEra user's figure relayed by Wccftech. The FSR 4 build/version is not stated. — [Wccftech, 2026-10-09](https://wccftech.com/helixsr-mod-dlss-3-7-steam-deck-amd-handhelds-faster-fsr-4/)
- [MEASURED, leaked 2025 INT8 build] On the Deck at 720p, FSR 4 cost about **4.8 ms more than FSR 3**. Horizon Forbidden West at 720p uplift over native: FSR 4 +16%, XeSS +33%, FSR 3 +44.6%. FSR 4 Balanced is +7% over Quality, Performance a further +14.5% (+25% total over native). In Control with RT at 720p, FSR 4 Balanced was +85% vs native at about 30 fps and only ~4% behind FSR 3. On the ROG Ally X at 720p/30 W in Cyberpunk: FSR 3 +24% vs FSR 4 +7.7%. These are NoobFeed's own tests with no methodology given; they closely match DF's published scenarios. — [NoobFeed, Oct 2025](https://www.noobfeed.com/hardware/amd-fsr4-int8-upscaling-consoles-gpus)
- [MEASURED, second-hand from Digital Foundry] DF's leaked-INT8 video (Oct 2025), as quoted on a forum: on the Deck in Performance mode FSR 4 INT8 gains ~28% over native vs 29–43% for FSR 3/XeSS, with "frequent drops in frame rate" in GPU-heavy scenes. I could not verify this against the DF original. — [NeoGAF thread, 2025-10-14 onward](https://www.neogaf.com/threads/digital-foundry-leaked-fsr4-int8-test-rdna-3-rdna-2-steam-deck-asus-rog-ally-nvidia-xbox-series-x-simulation.1689115/page-3)
- [MEASURED, single figure] Spider-Man Remastered, Ultra Performance: FSR 3 "could hit 90 FPS", FSR 4 "was around 70" (≈11.1 → 14.3 ms, i.e. ~3.2 ms delta). Power draw was described only qualitatively ("higher battery drain"). — [Steam Deck HQ, 2025-09-16](https://steamdeckhq.com/news/we-can-now-use-fsr-4-on-the-steam-deck-for-better-visuals-with-a-power-tradeoff/)
- [MEASURED, fps only] Using OptiScaler via Decky with FG off at 800p: Spider-Man (Medium) 30–43 fps, ~29 fps in the hardest areas, with FSR 4 on DLSS-Quality input. Black Myth: Wukong (lowest) ~30 fps. Horizon Forbidden West (very low, FSR 4 Performance) 24–30 fps. Ultra Performance was "too blurry". — [NoobFeed, 2026-01-28](https://www.noobfeed.com/hardware/fsr4-steam-deck-tested-aaa-games)
- [MEASURED, Deck, 2026] OptiScaler 0.9.4-final with `Fsr4Update=true`, `Fsr4ForceEnableInt8=true` and `Dx12Upscaler=fsr31` "starts successfully" with FSR 4.1.1 INT8 on the Deck in Cyberpunk 2077. Open bug: the watermark cannot be disabled. — [OptiScaler issue #1078](https://github.com/optiscaler/OptiScaler/issues/1078)

**Quality vs FSR 3.1**
- [MEASURED, RDNA3] FSR 4.1 Performance at 4K generally looks "much better" than FSR 3.1 Quality. At 1440p output, FSR 4.1 Balanced (~850p input) beats FSR 3.1 Quality in "the vast majority of scenes", and the reviewer found no case where 4.1 was worse at the same mode. INT8 and FP8 look near-identical down to ~850p input, but INT8 "may be slightly worse in a handful of edge cases at low render resolutions". Equal-fps example (Mafia, 4K): FSR 4.1 Performance 66 fps vs FSR 3.1 Quality 61 fps. Counter-example: in Horizon Zero Dawn Remastered, FSR 4.1 Performance was **slower** than FSR 3.1 Quality. — [TechSpot, 2026-07-02](https://www.techspot.com/article/3142-amd-fsr-4-upscaling-rdna-3/)
- [MEASURED, qualitative, Deck] FSR 3 shows "very pixelated, shiny visuals" and sparkle, and FSR 4 removes them with slight morphing on branches (Hell is Us). Distant windows are much sharper (Spider-Man), Hogwarts is much less blurry and shimmery, and Cyberpunk shimmers less. In KCD2 the gain is hard to see in stills. — [Steam Deck HQ, 2025-09-16](https://steamdeckhq.com/news/we-can-now-use-fsr-4-on-the-steam-deck-for-better-visuals-with-a-power-tradeoff/)
- [MEASURED, qualitative, Deck] FSR 4 is better than FSR 3.1 in every tested title: "more stable reconstruction, steadier edges, less breakup in fast motion". In Wukong, FSR 3.1 showed noise and pixel breakup on clouds, particles and crowds. — [NoobFeed, 2026-01-28](https://www.noobfeed.com/hardware/fsr4-steam-deck-tested-aaa-games)
- [News] An INT8 ghosting problem on RX 6000 (RDNA2) was "significantly" reduced in a March 2026 OptiScaler-team update (the "4.0.2b" INT8 build line), but the fix is "not guaranteed to fix all ghosting". — [Tom's Hardware, 2026-03-19](https://www.tomshardware.com/pc-components/gpus/optiscaler-team-fixes-int8-fsr-4-ghosting-on-rx-6000-series-gpus-adds-support-for-the-latest-adrenalin-drivers)

**Big cost-reduction lead**
- [MEASURED, RDNA2 BC-250, community fork] FSR 4 fork 4.0.0-rc9 (2026-09-11) adds "integer-processing optimizations" and moves the INT8 optimizations into a portable FidelityFX DLL. Median isolated FSR 4 dispatch: **1080p 7.13 → 3.93 ms; 1440p 11.51 → 5.92 ms (−49%); 4K 25.72 → 12.08 ms**. The fork reports 348 shaders with matching output and 220 automated tests passing. It targets Linux with Mesa and GE-Proton. The Steam Deck is not tested or mentioned, and nothing has been merged upstream. — [Guru3D, 2026-09-14](https://www.guru3d.com/story/optimized-fsr-4-nearly-halves-upscaling-time-on-amd-repurposed-bc250-mining-board/)

### Inferences
- **FSR 4 INT8 cost is roughly fixed per output resolution.** BC-250 time scales with output pixels (1080p→4K is 4x the pixels and ~3.6x the time), so lowering internal resolution barely reduces it. At 800p on the Deck, ~4.5 ms is about **20% of the 22.2 ms budget**, which leaves ~17.7 ms for the game itself. That is why FSR 4 is a net loss in light games and close to free in heavy ones: Control RT was only ~4% behind FSR 3 because the fixed cost is small next to a 33 ms frame.
- Estimated FSR 2/3.1 cost on the Deck at 800p: **~0.8–1.6 ms**. Basis: AMD's table shows RX 6650 XT 0.5–0.6 ms at 1080p; the Deck has ~3.2x less bandwidth (88 vs 280 GB/s) and ~6.5x less compute; 800p is 49% of 1080p's pixels. This is an inference, not a measurement. FSR 4's premium on the Deck is therefore about **3–3.5 ms per frame**, consistent with SDHQ's Spider-Man delta of ~3.2 ms.
- The 2025 leaked build (≈+4.8 ms over FSR 3 at 720p) and the 2026 figure (~4.5 ms total at 800p) suggest INT8 builds and RADV have improved, but methods differ. Treat both as ±1 ms order-of-magnitude numbers until DeckForge measures them itself with timestamp queries.
- If the BC-250 rc9 integer optimizations carry over to the Deck's RDNA2 GPU (BC-250 is also RDNA2), FSR 4 at 800p could drop to **~2.3–2.5 ms**. That would change the trade-off decisively in FSR 4's favour. **Top experiment for DeckForge.**
- Official AMD support for the Deck may land either as the RDNA2 path (early 2027) or as the "lighter handheld model" (end of 2026). The lighter model could beat the current INT8 cost, but that is unconfirmed.
- Unofficial INT8 on RDNA2 still carries **ghosting and artifact risk** (Tom's HW, Wccftech via igor'sLAB). DeckForge's quality scoring must include temporal and ghosting metrics, not just still-frame SSIM/FLIP.

### Gaps
- No primary Digital Foundry source with Deck ms figures was retrieved; only forum and secondary summaries.
- No controlled Deck measurement of **FSR 4.1.1 specifically** (vs 4.0.x INT8) in ms, and no power-draw (W) numbers anywhere.
- No ms measurement of FSR 3.1 on the Deck itself (only an estimate from AMD's desktop table).
- Unknown whether stock Valve Proton (10/11) exposes any FSR 4 RDNA2 path or env var. The only evidence is the Proton Experimental depot leak.
- No independent quality study at true Deck input resolutions (400–533p). TechSpot's lowest was ~850p input.

---

## Q2. XeSS 2.x (DP4a) on RDNA2 / Steam Deck: cost and quality

### Takeaway
XeSS's DP4a path runs on the Deck. In the available tests it is a **middle option**: heavier than FSR 3.1, lighter than FSR 4 INT8, and sharper and more detailed than FSR 3 but with edge instability and haloing. Reviewers recommended it as the balanced pick in at least one Deck title. No direct ms measurement exists.

### Cited Findings
- [DOC] XeSS Super Resolution "boosts frame rates on **all GPUs** with SM 6.4 (DP4a) support". — [Intel XeSS README](https://github.com/intel/xess)
- [DOC] OptiScaler bundles **XeSS 3.0.1** (since v0.9.1/0.9.3) and offers XeSS as an output on DX12 and Vulkan ("XeSS 2.x" listed for Vulkan). The native DX11 XeSS output is **Arc-only**; non-Arc GPUs need `xess_12` (DX11-on-12 interop). The ini's `NetworkModel` option "currently doesn't seem to do anything". — [OptiScaler releases](https://github.com/optiscaler/OptiScaler/releases); [OptiScaler README](https://github.com/optiscaler/OptiScaler); [OptiScaler.ini](https://github.com/optiscaler/OptiScaler/blob/master/OptiScaler.ini)
- [MEASURED, Deck, 720p HFW, leaked-FSR4 era] Uplift over native: XeSS +33%, FSR 3 +44.6%, FSR 4 +16%. — [NoobFeed, Oct 2025](https://www.noobfeed.com/hardware/amd-fsr4-int8-upscaling-consoles-gpus)
- [MEASURED, Deck, Red Dead Redemption] In-game FXAA ~76 fps vs XeSS (via OptiScaler) ~61 fps; FSR 4 "costs more performance than XeSS" (no fps given). Quality: FXAA very unstable; FSR 3 too soft and loses fine textures; XeSS keeps more detail but shows "instability at high-contrast edges" and a possible halo against the sky; FSR 4 handles contrast best. **Recommendation [ADVICE]: XeSS for general play**, with OptiScaler sharpening 0.25–0.3 (0.4 used in testing) and a fixed Quality mode rather than dynamic resolution. — [NoobFeed, 2025-12-29](https://www.noobfeed.com/hardware/red-dead-redemption-steam-deck-xess-fsr4)
- [Second-hand DF] On the Deck, FSR 3 and XeSS gains ranged ~29–43% depending on scene, vs ~28% for FSR 4 INT8. — [NeoGAF thread](https://www.neogaf.com/threads/digital-foundry-leaked-fsr4-int8-test-rdna-3-rdna-2-steam-deck-asus-rog-ally-nvidia-xbox-series-x-simulation.1689115/page-3)

### Inferences
- The RDR figures imply ~3.2 ms for XeSS over FXAA (13.2 → 16.4 ms). The internal resolution was described only as "native", so this may be XeSS at native-AA ratio. Taken with the HFW ordering (FSR 3 > XeSS > FSR 4 in uplift), XeSS DP4a on the Deck likely costs **~2–3 ms at 800p**, between FSR 3.1 (~1–1.5 ms est.) and FSR 4 INT8 (~4.5 ms). Inference only.
- If the BC-250-style FSR 4 optimization reaches the Deck (~2.5 ms), XeSS loses its niche, since FSR 4 would cost about the same and look better.
- In DX11 games XeSS needs the DX11-on-12 interop, which OptiScaler says costs up to ~10%. That makes XeSS less attractive in DX11 titles on the Deck.

### Gaps
- No isolated XeSS ms measurement on the Deck or any RDNA2 iGPU, and no XeSS 2/3 vs XeSS 1.3 comparison on RDNA2.
- No quality comparison of XeSS vs FSR 4 INT8 at matched frame time on the Deck.

---

## Q3. FSR 3.1, TSR (UE5), game-native TAAU, FSR 1 / NIS / SGSR via gamescope, Lossless Scaling LS1: when each is best

### Takeaway
On the Deck, the choice comes down to how much of the frame budget is left. **FSR 3.1 or TSR** is the cheap temporal default (~1–2 ms, more shimmer). **FSR 4 INT8** buys the most quality for ~4.5 ms. **Gamescope spatial filters** (FSR 1 / NIS / SGSR) are near-free and suit games with no temporal upscaler, or a second-stage scale. Lossless Scaling's LS1 **is not documented as available** on Linux.

### Cited Findings
- [DOC] AMD's FSR 2 cost table (no sharpening): at 1080p output, RX 6650 XT 0.6/0.6/0.5/0.4 ms (Q/B/P/UP); RX 590 1.3/1.2/1.1/0.9 ms; Vega 56 1.0/0.9/0.8/0.7 ms. Working set at 1080p Quality is ~115 MB. Cost depends mostly on output resolution, not mode. — [FSR2 README](https://github.com/GPUOpen-Effects/FidelityFX-FSR2)
- [MEASURED, qualitative] FSR 3.1 is "weakest at lower resolutions and lower quality modes". — [TechSpot, 2026-07-02](https://www.techspot.com/article/3142-amd-fsr-4-upscaling-rdna-3/)
- [ADVICE, UE5 dev blog] For UE5 on the Deck: TSR with `r.TemporalAA.Upscaler=1` and `r.ScreenPercentage=75`. It recommends **FSR 2 as the primary upscaler on the Deck** (via plugin), dynamic resolution 60–85%, and "dropping to 1024x640 internal" from 1280x800. No measurements were given. — [StraySpark, 2026-04-01](https://www.strayspark.studio/blog/shipping-60fps-ue5-steam-deck)
- [DOC] gamescope filters: `-F fsr` (FSR 1.0), `-F nis` (NVIDIA Image Scaling 1.0.3), **`-F sgsr` (Snapdragon Game Super Resolution 1 with RCAS)**, plus linear, nearest and pixel. The game renders at `-w/-h` and gamescope outputs at `-W/-H`. — [gamescope README](https://github.com/ValveSoftware/gamescope); [gamescope main.cpp](https://github.com/ValveSoftware/gamescope/blob/master/src/main.cpp)
- [DOC] OptiScaler's DX11 and Vulkan paths to DX12-only upscalers (FSR 3.1 DX12, FSR 4, XeSS on non-Arc) use a background DX12 device, with "a performance penalty up to 10-ish %". Native options exist: DX11 `fsr22`/`fsr31`; Vulkan `fsr21`/`fsr22`/`ffx` (FSR 2.3/3.1). — [OptiScaler README](https://github.com/optiscaler/OptiScaler); [OptiScaler.ini](https://github.com/optiscaler/OptiScaler/blob/master/OptiScaler.ini)
- [MEASURED, Deck] Using the in-game FSR 3 in RDR, FSR 3 was "too soft". — [NoobFeed, 2025-12-29](https://www.noobfeed.com/hardware/red-dead-redemption-steam-deck-xess-fsr4)

### Inferences
**Decision matrix for the Deck at 800p, 45 fps target** (costs are estimates unless marked)

| Option | Est. GPU cost @800p | Quality at Deck res | Injection | Best when | Risk |
|---|---|---|---|---|---|
| FSR 4.1.1 INT8 | **~4.5 ms [MEASURED, community]**; ~2.5 ms if BC-250 optimizations port | Best available; fixes shimmer and distant detail | Proton-CachyOS auto-upgrade for FSR 3.1+ games, or OptiScaler (`Fsr4ForceEnableInt8`) / Decky Framegen | Game renders ≥ ~27 ms native and has headroom after a resolution drop; FSR 3.1 or DLSS inputs exist | Unofficial; ghosting/artifacts on RDNA2; Tier I if via OptiScaler |
| HelixSR (DLSS 3.7 CNN) | **~3.5 ms [MEASURED, community]** | Below FSR 4, well above FSR 3 (one user) | DX12 FSR 3.1 replacement; OptiScaler for others | Experimental only | Licensing unknown; days old |
| XeSS (DP4a) | ~2–3 ms (inferred) | More detail than FSR 3; edge instability, halos | In-game, or OptiScaler output | FSR 4 too costly but FSR 3 shimmer unacceptable | DX11 needs interop (−~10%) |
| FSR 3.1 / FSR 2 | ~0.8–1.6 ms (inferred from AMD table) | Shimmer and pixelation at low input | In-game, or OptiScaler | Tight budgets; CPU-bound games | Weakest at <540p input |
| UE5 TSR | No Deck data | No Deck data | `Engine.ini` CVars | UE5 games without FSR/XeSS; DRS | Unknown cost |
| Game-native TAAU | No data | Varies | In-game | Only temporal option exposed | — |
| gamescope FSR1/NIS/SGSR | Near-free (no figure found) | Spatial; cannot remove aliasing | Steam scaling filter / gamescope flags | No temporal upscaler; second stage after a temporal upscale | None (Tier S) |
| Lossless Scaling LS1 | n/a | n/a | Not documented on Linux | — | — |

- Gamescope's spatial filters work on the finished frame and are **Tier S** (compositor level, no injection). A two-stage chain is legitimate: temporal upscale to an intermediate size, then gamescope FSR 1 or SGSR to 800p. It is untested on the Deck in any source found.
- SGSR in gamescope plausibly relates to Valve's Snapdragon-based hardware (Steam Frame). This is an inference, not confirmed.

### Gaps
- **No ms data for UE5 TSR or game-native TAAU on the Deck**, and none for gamescope FSR 1/NIS/SGSR.
- **LS1 status on Linux was not verified.** lsfg-vk is documented (compendium) as Lossless Scaling *frame generation*. I found no source saying LS1 *upscaling* is available through it. The lsfg-vk README URL returned 404 (repo likely moved).
- No measured FSR 3.1 ms on the Deck.

---

## Q4. OptiScaler: current version and features on Linux, install methods (Decky Framegen), anti-cheat risk

### Takeaway
The latest OptiScaler stable is **v0.9.4 (18 Jul 2026)**. It bundles FSR 4.1.1 (FFX SDK 2.3), adds `Fsr4ForceEnableInt8` (INT8 on unsupported GPUs, including the Deck), XeSS 3.0.1, Nukem's dlssg-to-fsr3, RCAS/depth-aware sharpening and mip-bias overrides. On the Deck it is installed manually or through **Decky Framegen**, whose RDNA2 FSR 4.1.1 path is still in **pre-release** (0.16.x-pre, late June 2026). OptiScaler's own README says **never use it in online games** (ban risk). It is Tier I in DeckForge's safety model.

### Cited Findings
**Versions and features**
- [DOC] **v0.9.4 (18 Jul 2026, "Latest")**: FSR 4.1.1 (FFX 2.3) with INT8 official on RDNA3 dGPUs. New `Fsr4ForceEnableInt8` forces INT8 on unsupported GPUs. It advises **RDNA2 Windows users to stay on FSR 4.0.2c** (not bundled). On Linux it tries INT8 on RDNA3. "Proton 11 should enable VK w/Dx12 FSR4". FSR4-FG needs Mesa 25.2+ and a Windows 11 prefix. It bundles Nukem's dlssg_to_fsr3 0.130 and fixes FSR-FG falling back to FSR3-FG under OptiFG. — [OptiScaler releases](https://github.com/optiscaler/OptiScaler/releases)
- [DOC] **v0.9.3 (18 Jun)**: bundles FFX 2.2 SDK + XeSS 3.0.1; FSR4 on RDNA4 by default; INT8 "not bundled and is needed for non-RDNA4 cards". **v0.9.2a (17 May)**: hooks the FSR 4 SDK at proxy level; Depth-Adaptive sharpening moved to an RCAS kernel. **v0.9.1 (27 Apr)**: Depth Aware Sharpening; fixed Vulkan extension spoofing for DXVK/VKD3D; fixed the disappearing Linux overlay; requires a Proton with VKD3D supporting FSR 4.1/FFX 2.2. **v0.9 (1 Apr)**: added FSR 2 DX11/Vulkan inputs and XeSS DX11 inputs; FG rewrite with separate FG inputs and outputs (XeFG+XeLL, FSR4-FG, OptiFG for XeFG); RCAS and Output Scaling for Vulkan upscalers; FSR 4.0.0 ML-FG is RDNA4 only; MFG is Arc only. — [OptiScaler releases](https://github.com/optiscaler/OptiScaler/releases)
- [DOC] Inputs: games with DLSS2+/FSR2+/XeSS. Outputs: **DX11**: fsr22, fsr31, xess (Arc), xess_12, fsr21_12, fsr22_12, ffx_12 (FSR 2.3/3.1/4.x), dlss. **DX12**: xess, fsr21, fsr22, ffx (FSR 2.3/3.1/4.x), dlss. **Vulkan**: fsr21, fsr22, ffx (FSR 2.3/3.1), xess, ffx_12 (FSR 4 via VK-on-12), dlss. FSR 4 is "officially RDNA4 and RDNA3 dGPUs only". — [OptiScaler.ini](https://github.com/optiscaler/OptiScaler/blob/master/OptiScaler.ini); [README](https://github.com/optiscaler/OptiScaler)
- [DOC] FSR 4 knobs: `Fsr4ForceModel` (0 = auto, 1 = FP8, 2 = INT8; "driver has a FSR 3 fallback" if you force FP8 on unsupported GPUs); `Fsr4Preset` 0–5 (Native AA, UQ/Q, Balanced, Performance, DRS, UP), which selects the internal model; `Fsr4EnableWatermark`; `Fsr4DoNotLoadAmdxc64`. — [OptiScaler.ini](https://github.com/optiscaler/OptiScaler/blob/master/OptiScaler.ini)
- [DOC] Frame gen: `FGInput` = nofg/dlssg/nvngxfg/fsrfg/upscaler/fsrfg30/xefg; `FGOutput` = nofg/fsrfg/xefg/dlssg. OptiFG (inject FG into DX12 games without native FG) is **DX12 only**, experimental, and needs HUDfix for FSR3-FG. Fakenvapi enables Anti-Lag 2 / LatencyFlex / XeLL. — [OptiScaler.ini](https://github.com/optiscaler/OptiScaler/blob/master/OptiScaler.ini); [README](https://github.com/optiscaler/OptiScaler)
- [DOC] **Anti-cheat**: "**Do not use this mod with online games.** It may trigger anti-cheat software and cause bans!" The README also says the team has **no official website and no official manager app**. — [OptiScaler README](https://github.com/optiscaler/OptiScaler)
- [News] "OptiScaler Client 1.0.7" (2026-09-16) is an open-source manager with Linux downloads. It does DLL swapping and imports for INT8/FP8/custom FSR 4 DLLs "without requiring an OptiScaler install", has recommended per-game configs, and offers FG/MFG multipliers up to x6. No anti-cheat warning. **Conflict:** the OptiScaler README says the team has no official manager app, so this client is third-party. — [GamingOnLinux, 2026-09-16](https://www.gamingonlinux.com/2026/09/optiscaler-client-1-0-7-brings-major-improvements-for-fsr-4-and-improved-recommended-game-configs/); [OptiScaler README](https://github.com/optiscaler/OptiScaler)

**Install on the Deck (Decky Framegen)**
- [DOC] Decky Framegen: latest stable **v0.15.6 (31 May)**. Pre-releases: **v0.15.8-pre (23 Jun)** upgrades bundled OptiScaler 0.9.3 → 0.9.4-pre1 and adds FSR4 variants `rdna23-int8`, `rdna4-native` and `rdna34-official-411`. **v0.16.0-pre1 (23 Jun)** adds an experimental "4.1.1 Valve RDNA2 compatibility runtime" with **Valve `amdxcffx64.dll` 2.3.0.2913** and `Fsr4ForceModel=2`. **v0.16.3-pre (26 Jun)** bundles an **RDNA2-specific `amdxc64.dll`** and applies RDNA2 ini overrides. — [Decky Framegen releases](https://github.com/xXJSONDeruloXx/Decky-Framegen/releases)
- [Community report] With OptiScaler 0.9.4 Final, `Fsr4ForceEnableInt8=true` "enables FSR 4.1.1 Int8 on all supported and unsupported GPUs". Reported working on the Steam Deck (RDNA2, SteamOS) and ROG Ally (Bazzite), with no FSR 3.1 fallback. Plugin injection fails in some games (MGS Delta; UE5 path detection), and the maintainer recommends a manual install in those cases. — [Decky Framegen issue #204](https://github.com/xXJSONDeruloXx/Decky-Framegen/issues/204)
- [Guide] Workflow from 2025: install via Decky; map a back button to Insert to open the OptiScaler overlay; set the trackpad as mouse; choose "FSR 3.x.x/4" as the upscaler. — [Steam Deck HQ, 2025-09-16](https://steamdeckhq.com/news/we-can-now-use-fsr-4-on-the-steam-deck-for-better-visuals-with-a-power-tradeoff/)

### Inferences
- For DeckForge, OptiScaler is the **broadest reconstruction switchboard** (any DLSS/FSR2+/XeSS game → FSR 4 INT8 / XeSS / FSR 3.1, plus RCAS and mip bias). It is DLL injection, so it **must stay Tier I**: opt-in per game and never in anti-cheat titles.
- The Proton-CachyOS route (driver-DLL override of `amdxcffx64.dll` for games that already ship FSR 3.1) mirrors AMD's own driver-override mechanism and does not inject into the game binary. It is probably lower risk than OptiScaler, but it is still a non-stock Proton. Whether anti-cheat flags it is **unverified**. Do not move it to Tier S without evidence.
- Because Decky Framegen's RDNA2 path is pre-release and uses Valve-sourced DLL builds of unclear provenance, DeckForge should **pin exact OptiScaler and DLL versions** per game profile and verify them by hash.
- The Valve-built `amdxcffx64.dll` 2.3.0.2913 and the RDNA2-specific `amdxc64.dll` imply Valve has an internal RDNA2 FSR 4.1.1 path. This is inference from file names in Decky Framegen release notes, with no Valve statement.

### Gaps
- The OptiScaler wiki pages (Linux install, Steam Deck, compatibility list) were not fetched. Exact DLL proxy names and `WINEDLLOVERRIDES` used on the Deck are not confirmed here.
- No data on OptiScaler's own CPU/GPU overhead on the Deck (beyond the "up to ~10%" interop note for DX11/Vulkan → DX12).
- No reported bans involving Proton-level FSR4 DLL overrides; absence of evidence only.

---

## Q5. ML-based and new reconstruction approaches for RDNA2 handhelds (Redstone, community ML, Valve's work)

### Takeaway
Three live threads matter for the Deck: (1) **HelixSR** (Oct 2026), which runs NVIDIA's DLSS 3.7 CNN model as plain DX12 compute shaders and measured *faster than FSR 4* on the Deck; (2) the **community FSR 4 integer optimizations** (BC-250 fork), which halve dispatch time on RDNA2 silicon; and (3) AMD's promised **lighter handheld FSR 4**. The rest of Redstone (ML frame gen, ray regeneration, radiance caching) has no evidence of usefulness on RDNA2. Valve's visible work targets the Steam Machine (RDNA3-class) through vkd3d-proton and Proton.

### Cited Findings
- [MEASURED, community; news 2026-10-09] **HelixSR** by "lonewolf0622" (GitHub, released ~2026-10-07) is a drop-in replacement for the **FSR 3.1 upscaler on D3D12** that outputs **DLSS Preset E (DLSS 3.7, last CNN model)** run "as plain DirectX 12 compute shaders". It needs no NVIDIA driver, CUDA or ROCm, and works on the Deck through Proton/vkd3d-proton. It is **D3D12 only, with no Vulkan**; non-FSR 3.1 games need OptiScaler. Deck @1400 MHz: **~3.5 ms at 800p vs ~4.5 ms for FSR 4**; 1080p ~7 vs ~11 ms. Pragmata on the Deck: 34–40 fps in Performance mode. Quality: one user found it "not quite as good as FSR 4, but much better than FSR 3", while another suggested it can beat FSR 4 in ghosting-prone titles. Five updates in a few days added a single-file installer and a "Quality Super-Sampled Mode". Licensing and anti-cheat were not discussed. — [Wccftech, 2026-10-09](https://wccftech.com/helixsr-mod-dlss-3-7-steam-deck-amd-handhelds-faster-fsr-4/)
- [MEASURED, community] BC-250 FSR 4 fork rc9: ~49% lower FSR 4 dispatch time on RDNA2 via integer-processing optimizations (see Q1). — [Guru3D, 2026-09-14](https://www.guru3d.com/story/optimized-fsr-4-nearly-halves-upscaling-time-on-amd-repurposed-bc250-mining-board/)
- [CLAIM] AMD's "lighter" FSR 4 for handheld APUs is promised by the end of 2026, with targets unnamed and the Deck not mentioned. — [Notebookcheck, 2026-10-07](https://www.notebookcheck.net/FSR-4-special-version-to-boost-gaming-performance-on-handhelds-coming-this-year.1418417.0.html); [SDHQ, 2026-10-08](https://steamdeckhq.com/news/amd-fsr-4-confirmed-for-handhelds-2026/)
- [CLAIM, 2025] Redstone components are ML upscaling, ML frame generation, Ray Regeneration and Neural Radiance Caching. They were built with AMD's **ML2CODE** (ROCm research project), which converts the neural core into compute shader code (HLSL/GLSL). AMD's stated plan is **RDNA4 only**. AMD's Chris Hall said a CUDA conversion would "probably" run on NVIDIA. Nothing confirms Redstone components run on RDNA2. — [PCGH, 2025-09-18](https://www.pcgameshardware.de/FidelityFX-Super-Resolution-Software-277617/News/FSR-4-Redstone-auf-alten-GPUs-1482347/)
- [DOC] Redstone ML frame gen on Linux: Proton-CachyOS `MLFG_UPGRADE` works on RDNA3 with the WMMA workaround. OptiScaler v0.9 says FSR 4.0.0 ML-FG is RDNA4 only, and v0.9.4 says FSR4-FG needs Mesa 25.2+ and a Win11 prefix. — [GOL, 2026-07-13](https://www.gamingonlinux.com/2026/07/proton-cachyos-version-11-0-20260702-brings-amd-fsr4-upgrades-pipewire-changes/); [OptiScaler releases](https://github.com/optiscaler/OptiScaler/releases)
- [DOC/news] Valve-side work: vkd3d-proton 3.0 has FSR 4 via cooperative-matrix/float8 with an INT8/FP16 emulation fallback for RDNA2/3 ([Guru3D, 2025-11-19](https://www.guru3d.com/story/vkd3dproton-30-adds-amd-fsr4-antilag-supports-older-rdna-gpus/)); an FSR 4.1.1 INT8 DLL briefly appeared in the Proton Experimental depot, and Valve is reportedly working with AMD on FSR 4 for the Steam Machine ([igor'sLAB, 2026-06-27](https://www.igorslab.de/en/valve-fsr-4-1-proton-experimental-rdna-3-3-5/)); DF measured FSR 4 on the Steam Machine (cut-down Navi 33) at e.g. Cyberpunk ~60 fps with dynamic res at 1620p output ([GameGPU summarising DF, 2026-07-10](https://en.gamegpu.com/news/zhelezo/testirovanie-fsr-4-na-konsoli-steam-machine-i-videokartakh-rdna-3)); gamescope gained an **SGSR 1 + RCAS** filter ([gamescope main.cpp](https://github.com/ValveSoftware/gamescope/blob/master/src/main.cpp)).

### Inferences
- **HelixSR is technically the most interesting new Deck option** (cheaper than FSR 4 at 800p). It carries probable **legal/licensing risk**: DLSS model weights are NVIDIA proprietary, and running them on non-NVIDIA hardware outside the DLSS SDK terms is likely not permitted. DeckForge should **not bundle or automate it** until its licensing and weight provenance are clear. At most, benchmark it privately as a quality/cost reference point.
- The BC-250 fork shows that FSR 4 INT8 cost on RDNA2 is **software-limited, not only hardware-limited**. That supports DeckForge treating "upscaler implementation version" as a search dimension, and suggests upstreaming or tracking these optimizations.
- ML frame gen and ray regeneration are irrelevant for the Deck's 45 fps native target. Frame gen is tracked separately per CLAUDE.md, and RT is rarely viable on the Deck.

### Gaps
- HelixSR GitHub repo, license and weight-source not found by search, so its legality is unverified.
- Whether the BC-250 rc9 fork runs on the Deck (Van Gogh) and its Deck cost: untested in any source.
- No Valve statement on FSR 4 for the Steam Deck specifically; no evidence of Valve-built ML upscaling for the Steam Frame.
- No academic or community ML upscaler other than HelixSR targeting RDNA2 handhelds was found.

---

## Q6. Sharpening (CAS/RCAS) tuning for small screens; negative LOD/mip bias when upscaling and how to set it

### Takeaway
The knobs exist at every layer: **gamescope** `--sharpness` 0 (max) to 20 (min), default 2; **OptiScaler** RCAS / depth-aware / motion-adaptive sharpening (default 0.3, range 0–1.3) plus a mip-bias override; **dxvk** `d3d11.samplerLodBias` (−2.0 to 1.0, added to the game's bias). AMD recommends a mip bias of `log2(render/display) − 1`, which is **−1.58 / −1.76 / −2.0 / −2.58** for Q/B/P/UP. Evidence specific to small screens is anecdotal: about **0.25–0.4** RCAS in one Deck title.

### Cited Findings
- [DOC] AMD formula: `mipBias = log2(renderResolution/displayResolution) − 1.0`. Quality −1.58, Balanced −1.76, Performance −2.0, Ultra Performance −2.58. AMD also suggests tuning the bias down for high-frequency textures that shimmer temporally. Apps should expose a sharpening slider. — [FSR2 README](https://github.com/GPUOpen-Effects/FidelityFX-FSR2)
- [DOC] dxvk: `d3d11.samplerLodBias` / `d3d9.samplerLodBias` is **added** to the app's own LOD bias, range −2.0 to 1.0 ("negative values may increase sharpness at the cost of shimmer"). `d3d11.clampNegativeLodBias` / `d3d9.clampNegativeLodBias` clamps negative bias to 0 after that. — [dxvk.conf](https://github.com/doitsujin/dxvk/blob/master/dxvk.conf)
- [DOC] vkd3d-proton's documented `VKD3D_CONFIG` options include nothing for sampler LOD bias (options listed: vk_debug, skip_application_workarounds, nodxr, dxr, dxr12, force_static_cbv, single_queue, no_upload_hvv, force_host_cached, no_invariant_position, etc.). — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/README.md)
- [DOC] OptiScaler `[Mipmap]`: `MipmapBiasOverride` (−15 to 15), `MipmapBiasFixedOverride`, `MipmapBiasScaleOverride` (use as multiplier), and `MipmapBiasOverrideAll`. By default it only overrides samplers that already have a bias below 0, i.e. the ones the game biased for upscaling. Older nightlies improved the anisotropic filtering and LOD bias overrides. — [OptiScaler.ini](https://github.com/optiscaler/OptiScaler/blob/master/OptiScaler.ini); [OptiScaler releases](https://github.com/optiscaler/OptiScaler/releases)
- [DOC] OptiScaler `[Sharpness]`: `Shader` = rcas | da (depth-based edge detection, less sharpening across object boundaries, more on distant objects) | lcda (local-contrast DA). `Sharpness` defaults to 0.3, range 0–1.0 (RCAS up to 1.3). `OverrideSharpness` replaces the game's DLSS sharpness. `[CAS]` adds motion-adaptive sharpness (default 0.4, range −1.3 to 1.3, threshold and scale limit) and contrast-based sharpening (0–2.0, "might cause glitches" at high values). — [OptiScaler.ini](https://github.com/optiscaler/OptiScaler/blob/master/OptiScaler.ini)
- [DOC] gamescope: `--sharpness` / `--fsr-sharpness` "from 0 (max) to 20 (min)", **default 2**. Super+I/O adjust it live. It applies to the FSR 1/NIS/SGSR filters. — [gamescope main.cpp](https://github.com/ValveSoftware/gamescope/blob/master/src/main.cpp)
- [ADVICE, Deck] OptiScaler sharpening 0.25–0.3 is suggested; 0.4 was used in testing in RDR. — [NoobFeed, 2025-12-29](https://www.noobfeed.com/hardware/red-dead-redemption-steam-deck-xess-fsr4)

### Inferences
- Pixel density: 1280x800 over 7.0" (LCD) ≈ 216 ppi and 7.4" (OLED) ≈ 204 ppi, viewed at handheld distance. Sharpening halos are less visible than on a TV, but so is softness. A starting range of **RCAS 0.2–0.4** (or gamescope 2–5) with depth-aware mode for foliage-heavy scenes is a reasonable search space, not an established optimum.
- DeckForge should set mip bias **per game and per upscaler mode**. The bias the game applies at 400p→800p (−2.0) can already be too aggressive on high-frequency textures (shimmer). Better tools: OptiScaler `MipmapBiasOverride` for injected games, dxvk `samplerLodBias` for DX11/DX9 Tier S titles, and the compendium's planned `vkCreateSampler` hook for DX12/Vulkan titles, since vkd3d-proton exposes no knob.
- Negative bias also costs bandwidth (higher-resolution mips), and bandwidth is often the Deck's limiter (compendium §2). Image-quality gains from bias must be scored against frame-time cost, not assumed free.

### Gaps
- No controlled study of optimal RCAS strength or mip bias at 800p on 7" handheld screens.
- vkd3d-proton: no documented LOD bias override found. Undocumented options or app profiles may exist (not checked in source).
- Steam's built-in per-game "FSR sharpness" slider mapping to gamescope values is not documented in the sources retrieved.

---

## Q7. Which internal resolution gives the best quality per ms at 800p on the Deck GPU?

### Takeaway
The evidence points to **~400–470p internal (Performance/Balanced) when using FSR 4 INT8**, because its ~4.5 ms cost is fixed by output resolution and must be recouped from rendering. With cheap upscalers (FSR 3.1/TSR), **~533–640p (Quality to 80%)** is the commonly advised range. **Ultra Performance (267p) is too blurry** in Deck tests. There is no rigorous quality-per-ms curve for the Deck; DeckForge would be first to produce one.

### Cited Findings
- [MEASURED, Deck, leaked INT8 2025] FSR 4: Balanced +7% fps over Quality; Performance a further +14.5% (+25% total over native). — [NoobFeed, Oct 2025](https://www.noobfeed.com/hardware/amd-fsr4-int8-upscaling-consoles-gpus)
- [MEASURED, Deck, qualitative] Spider-Man: switching the input from DLSS-Quality to DLSS-Performance (FSR 4 output) gave about +10 fps "with no clear quality loss". Horizon Forbidden West: Ultra Performance "too blurry". — [NoobFeed, 2026-01-28](https://www.noobfeed.com/hardware/fsr4-steam-deck-tested-aaa-games)
- [MEASURED, RDNA3 desktop] FSR 4.1 Performance (1080p→4K) generally beats FSR 3.1 Quality; FSR 4.1 Balanced at ~850p input beats FSR 3.1 Quality at 1440p; INT8 may be slightly worse "in a handful of edge cases at low render resolutions". — [TechSpot, 2026-07-02](https://www.techspot.com/article/3142-amd-fsr-4-upscaling-rdna-3/)
- [MEASURED] FSR 4 cost scales with output pixels (BC-250: 3.93 ms at 1080p vs 12.08 ms at 4K, optimized). — [Guru3D, 2026-09-14](https://www.guru3d.com/story/optimized-fsr-4-nearly-halves-upscaling-time-on-amd-repurposed-bc250-mining-board/)
- [ADVICE] UE5 on the Deck: 1024x640 internal (80%), dynamic res 60–85%, TSR or FSR 2. — [StraySpark, 2026-04-01](https://www.strayspark.studio/blog/shipping-60fps-ue5-steam-deck)
- [ADVICE] Use a fixed Quality mode rather than dynamic resolution with OptiScaler/XeSS (RDR). — [NoobFeed, 2025-12-29](https://www.noobfeed.com/hardware/red-dead-redemption-steam-deck-xess-fsr4)
- [MEASURED] FSR 4's relative penalty shrinks as base frame cost rises: Control RT at 720p, FSR 4 Balanced only ~4% behind FSR 3. Ally X Cyberpunk at 30 W: FSR 3 +24% vs FSR 4 +7.7%. — [NoobFeed, Oct 2025](https://www.noobfeed.com/hardware/amd-fsr4-int8-upscaling-consoles-gpus)

### Inferences
- **Break-even model for FSR 4 at 45 fps:** native-res render time R(800p) must drop by more than ~3–3.5 ms (FSR 4's premium over FSR 3.1) when going from the FSR 3.1 input resolution to the FSR 4 input resolution. Rendering cost scales roughly with pixel count for GPU-bound passes. If a game's 800p-native frame is ~30 ms GPU, then Quality (44% of the pixels) to Performance (25%) saves on the order of 5+ ms on the resolution-scaled share. So **FSR 4 Performance (400p) can match FSR 3.1 Quality (533p) on frame time while looking better**, consistent with TechSpot's desktop result. This is inference and must be validated per game.
- This only holds for **GPU-bound, resolution-scaled** frames. For CPU-bound or geometry/fixed-cost-heavy games (shadows, simulation), lowering internal resolution buys little, and FSR 4's fixed ~4.5 ms is a pure loss. DeckForge's diagnose step (CPU- vs GPU-bound, per-pass costs) should gate which upscaler gets searched.
- Practical search grid for DeckForge at 800p output: internal heights {400, 470, 533, 600, 640, 800} × upscaler {FSR 4 INT8, XeSS, FSR 3.1/TSR, native TAA + gamescope FSR 1} × RCAS {0.2, 0.3, 0.4} × mip bias {game default, AMD formula, formula +0.5}. Score by p99 frame time ≤ 22.2 ms first, then FLIP plus a temporal-stability metric.
- If the BC-250 optimization or AMD's lighter handheld model lowers FSR 4 to ~2–2.5 ms, the sweet spot shifts up to **Balanced/Quality (470–533p)**.

### Gaps
- No published quality-vs-ms curve for any upscaler at 800p output on the Deck; no objective metric (FLIP/SSIM/VMAF) comparisons at Deck resolutions.
- No measurement of how FSR 4 INT8 quality degrades below ~533p input; only "Ultra Performance too blurry" anecdotes.
- No Deck data separating GPU-bound vs CPU-bound behaviour per game under upscaling, which the break-even model depends on.
