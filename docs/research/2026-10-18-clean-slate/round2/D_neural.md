# Cluster D red-team: neural reconstruction (D1) and compositor restoration (D2)

Sources: Mesa main from the `chaotic-cx/mesa-mirror` GitHub mirror, fetched 2026-10-18. freedesktop GitLab and gpuinfo.org were blocked from this session. Also Valve gamescope master `6867f50` (2026-09-27, clean clone in the scratchpad), dxil-spirv and vkd3d-proton master, intel/xess, and LLVM.

## 0. What already runs on the Deck: the baseline D1 must beat

| Upscaler | Uses dot4 on the Deck? | Cost at 800p output | Evidence |
|---|---|---|---|
| FSR2 / 3.1 | no | 1.6–2.3 ms (est.) | AMD's table: 1080p Performance is 0.5 ms on an RX 6650 XT and 1.1 ms on an RX 590 ([FSR2 README](https://github.com/GPUOpen-Effects/FidelityFX-FSR2), perf table), scaled by ALU and pixel count. I found no direct Deck measurement. |
| XeSS 1.3+ DP4a | **yes** | ≈3.2–4 ms | RDR via OptiScaler at native 800p: XeSS 61 fps vs FXAA 76 fps, so ≈3.2 ms ([noobfeed, Dec 2025](https://www.noobfeed.com/hardware/red-dead-redemption-steam-deck-xess-fsr4); one scene, press test). RX 6800 XT, 1440p Quality: FSR 3.1 0.6 ms, XeSS 1.15 ms, FSR 4.1 INT8 1.48 ms ([gamegpu, 30 Jun 2026](https://en.gamegpu.com/news/zhelezo/fsr-4-1-na-radeon-rx-6800-xt-v-linux-rabotaet-luchshe-chem-na-windows), sourced from Reddit). Scaled by ALU (×3.5) that is 2.1 / 4.0 / 5.2 ms on the Deck. |
| FSR4 INT8 (leaked build) | yes | ≈4.5–5.2 ms | Spider-Man Ultra Performance: 90 fps → 70 fps vs FSR3, i.e. +3.2 ms ([steamdeckhq](https://steamdeckhq.com/news/we-can-now-use-fsr-4-on-the-steam-deck-for-better-visuals-with-a-power-tradeoff/)). Off-limits (legal). |
| TSR | no | ~1.2 ms (est., from Epic's 1.5 ms on PS5) | Engine-internal. OptiScaler only swaps DLSS/FSR/XeSS inputs ([README](https://github.com/optiscaler/OptiScaler)). |
| PSSR | n/a | — | Needs the PS5 Pro's ML hardware. Nothing comparable exists here. |

- gamescope master now also ships SGSR, a spatial upscaler (`src/rendervulkan.cpp:4370ff`).
- **D1's "FSR2 never uses dot4" advantage is gone, because XeSS already does.**
  - XeSS's cross-vendor path needs SM 6.4 DP4a ([intel/xess README:9](https://github.com/intel/xess); `doc/xess_sr_developer_guide_english.md:128`).
  - vkd3d-proton always enables `SPV_KHR_integer_dot_product` (`libs/vkd3d/device.c:10056–10057`).
  - dxil-spirv lowers `Dot4AddI8Packed` to `OpSDotKHR` + `IAdd` (`opcodes/dxil/dxil_arithmetic.cpp:1172–1192`).
  - ACO then emits `v_dot4_i32_i8` below GFX11 (`src/amd/compiler/instruction_selection/aco_select_nir_alu.cpp:2055–2060`).
- **XeSS 1.3 Performance mode is 2.3× per axis**, about 557×348 from 800p (dev guide:68–79). That is almost exactly D1's 512×320 operating point. So Intel has already shipped D1's thesis, generically.
- TechSpot (RX 6750 XT): FSR4 INT8 needs roughly two quality modes lower to match FSR3's speed ([TechSpot](https://www.techspot.com/article/3040-amd-fsr4-upscaling-older-radeon-gpu/)).

## 1. The compute claims

- **ACO emits `v_dot4_i32_i8` for `OpSDotKHR` on Van Gogh: [checked].**
  - `has_accelerated_dot_product` is true for VANGOGH. It excludes only NAVI10 and GFX1013 (`src/amd/common/ac_gpu_info.c:338–340`).
  - RADV reports 4x8 packed signed/unsigned dot products as accelerated (`radv_physical_device.c:1796, 2035–2039`).
- **INT4: [contradicted] on this stack.**
  - `v_dot8_i32_i4` exists in ACO's opcode table (`aco_opcodes.py:1242`), but no NIR op maps to it.
  - VK_KHR_shader_integer_dot_product has no 4-bit packed format.
  - So D1's "~0.8 ms with INT4" needs a Mesa patch, which can't ship on stock SteamOS.
- **The OLED reports gfx1033: [could not verify directly]; the indirect evidence is strong.**
  - The kernel maps GC IP 10.3.1 to `AMDGPU_FAMILY_VGH` (`drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c:3370–3371`).
  - Mesa maps that family only to CHIP_VANGOGH (`ac_gpu_info.c:732–734`).
  - The OLED's PCI ID is 1002:1435 ([F@H forum lspci](https://forum.foldingathome.org/viewtopic.php?p=367607)).
  - In LLVM, gfx1033 uses ISA 10.3.0, which includes Dot1/2/5/6/7/10 (`GCNProcessors.td:204–206`, `GCNFeatures.td:2270–2284`).
  - Bench check: `vulkaninfo` should show "RADV VANGOGH", and a `RADV_DEBUG=shaders` dump should contain `v_dot4_i32_i8`.
- **3.28 TMAC/s INT8: [checked as arithmetic, peak only].**
  - 8 CU × 64 lanes × 4 MAC × 1.6 GHz. It matches the per-lane rate of Xbox Series X.
  - With in-game GPU clocks of 1.3–1.6 GHz (est.), the peak is 2.7–3.3 TMAC/s.
- **40% utilization: optimistic.** My estimates are 15% pessimistic, 25% central, 40% optimistic, for these reasons (all est.):
  - Requantize and pack costs about 70 VALU ops per 576 dot4 in a 16-channel 3×3 layer. That caps dot issue at about 85% even before LDS loads and barriers.
  - Activations of 1.3–2.6 MB per layer overflow the 1 MB L2, so every layer round-trips to DRAM.
  - The deepest UNet level (64×40) gives about 5 waves per CU, which hides latency badly.
  - About 20 dispatch boundaries add fixed overhead.

## 2. D1 budget, redone

| | Pessimistic | Central | Optimistic |
|---|---|---|---|
| D1 cost (1.5 GMAC) | 15% @ 1.3 GHz → 3.75 ms + 1.0 = **4.75 ms** | 25% @ 1.5 GHz → 1.95 + 1.0 = **2.95 ms** | 40% @ 1.6 GHz → 1.15 + 0.8 = **1.95 ms** |
| Saving from 640×400 → 512×320 | 2.3 ms | 3.0 ms | 3.5 ms |
| Net vs FSR2 at 640×400 (FSR2 ≈ 1.8 ms) | **−0.65 ms (a loss)** | **+1.85 ms** | **+3.35 ms** |

- **[contradicted]: the "15 ms pixel-proportional at 640×400" anchor.** The cluster's own console-port budget gives 18.9–21.8 ms of pixel-proportional work at 960×600 (`1_console_port.md:11–14`). That is 8.4–9.7 ms at 640×400, and a 36% pixel cut saves 3.0–3.5 ms (linear) or ~2.3 ms (sub-linear).
- The net figures assume quality parity at a 2.5× ratio, which is the unproven part.
- **Double-counting:**
  - Cluster A (VRS) and clusters B/E shrink the same pixel-proportional work. After about 2 ms from A, D1's central gain drops to about +1.3 ms.
  - D2 stacked on D1 gains less.
- **Power:** dense INT8 work raises GPU power (steamdeckhq reports higher battery draw with FSR4). At a fixed 15 W this can lower clocks for the rest of the frame. CPU-bound hub scenes gain nothing.

## 3. Is per-game training worth it?

The cited evidence is misread.
- **NAS (OSDI'18) [contradicted as evidence]:**
  - Its "generic" model was trained on NTIRE 2017 natural images.
  - Its content-aware models used "the entire video for training" (§7.1), i.e. they trained on the test content ([PDF](https://www.usenix.org/system/files/osdi18-yeo.pdf)).
  - That shows a domain gap plus training on the test set, not per-game vs multi-game.
- **River:** +1.81 dB over generic SR that was not trained on game content. Same confound ([arXiv 2501.06880](https://arxiv.org/html/2501.06880v1)).
- **GameSR is the cleanest test** ([SFU PDF](https://www.cs.sfu.ca/~mhefeeda/Papers/tg26_GameSR.pdf)):
  - Per-title model vs a joint CS2+OW2 model: 37.80 vs 37.53 dB on CS2, and 38.81 vs 38.74 dB on OW2.
  - So per-game training buys **0.07–0.27 dB** over a model trained on game content. Running a model on a game it never saw costs 1.6–3.2 dB.
  - What matters is game-like training data, not *this game's* data. I expect under 0.1 JOD from per-game adaptation (est.).
- DLSS 1 → DLSS 2 teaches the same lesson: temporal inputs plus broad data beat per-title models.
- **Training data needed (est.):**
  - Adapters (1–4 KB): 1–3k frames across 20 or more locations.
  - A full ~150K-parameter per-game model: 5–20k frames.
- **Who makes the references:**
  - Motion-aligned supersampled ground truth needs control of jitter and camera. That means Tier I injection on a PC, or a deterministic replay.
  - Anti-cheat titles only allow static views (photo mode or pause, at a render scale above 100%). So they give no motion data.

## 4. D2

- **Already done:**
  - gamescope's FSR1 (EASU + RCAS), NIS and SGSR run only when the image needs scaling (`src/steamcompmgr.cpp:3236–3238`).
  - At a 1:1 800p output, the only sharpening is the game's own slider, or ReShade CAS via [Reshadeck](https://github.com/safijari/Reshadeck).
- **The Low-vs-High premise fails mechanically.**
  - High differs from Low mostly in non-local content: shadows, AO, GI, LOD and foliage density.
  - An 11×11 RAISR filter or a LUT network cannot add missing shadows.
  - Trained on pairs that don't line up (different LOD and foliage), it learns blur plus a tone shift.
  - Rescue: use same-preset pairs (deployed TAAU vs the maximum render scale). That turns D2 into "undo this game's upscaler blur", which is what a tuned sharpener already does.
  - Without motion vectors it cannot tell TAA shimmer from detail. Sharpening amplifies the flicker, and ColorVideoVDP penalizes it.
- **Published game-frame results:** GameSR and River restore compressed streaming video and compare against bicubic. I found nothing that compares a learned filter with a tuned CAS on TAAU output. My expectation is 0–0.15 JOD over tuned CAS/RCAS (est.).
- **Latency: [checked mechanism; magnitude could not verify].**
  - gamescope submits the ReShade pass on the *general* queue (`src/reshade_effect_manager.cpp:1015`).
  - The compositor then waits on the CPU for it to finish (`g_device.wait(seq)`, `src/rendervulkan.cpp:4336–4337`) before recording the composite.
  - Built-in filters run on the compute-only realtime-priority queue instead (`src/rendervulkan.cpp:400, 542–561, 1305`).
  - So ReShade adds at least its own GPU time to every present, and it can queue behind the game's graphics work. Reshadeck's README warns of "severe performance degradation".
  - A native pass means patching Valve's gamescope. That binary sits on a read-only root filesystem and is overwritten by updates, so it has to be upstreamed.
  - Compute passes do work through the ReShade path (`src/reshade_effect_manager.cpp:1422–1440`).
- **Cost (est.):** RAISR as a native pass is 0.3–0.6 ms with LDS tiling. Through ReShade, the total is 1.5 / 0.8 / 0.4 ms (pessimistic / central / optimistic).
- **Tier S [checked]:** it runs in the compositor process, so it is allowed for anti-cheat games. But the HUD is part of layer 0, so the filter changes HUD text.
- **Double-counting:** sharpness is already a knob in cluster E's search, and the mid-scale contrast idea (3_perception #5) wants the same filter slot. Score D2 on top of E's best profile.

## 5. Legal (I'm not a lawyer; cautious reading)

- **Training on frames:** it copies copyrighted game output, and fair use is unsettled in the US. EULAs may forbid it. Injecting a capture tool into anti-cheat games breaks their terms of service.
- **Shipping weights:**
  - Adapters of a few KB are unlikely to contain protectable expression.
  - LUTs or CNNs of 100–150 KB could memorize HUD glyphs and logos. Test for memorization before shipping.
  - Cleanest route: fit on the user's own device from their own copy and ship only code. RAISR's least-squares fit takes minutes on Zen 2, which makes D2 legally clean. D1 can't train on-device beyond adapters.
- **Teachers:**
  - Use supersampled ground truth only.
  - Never use or distill the leaked FSR4 INT8 ([igor'sLAB](https://www.igorslab.de/en/amd-fsr-4-leak-how-a-botched-github-push-reshuffles-the-cards/): an "executable INT8 version" leaked in a botched GitHub push).
  - I could not verify whether AMD's or NVIDIA's SDK licences allow using official FSR4 or DLSS output as a teacher. Treat it as prohibited until checked.

## 6. Post-June-2026 claims

- **"FSR4 for RDNA2 including the Deck, early 2027": [partly contradicted].**
  - AMD's Jack Huynh announced FSR 4.1 for RX 7000 in July 2026 and for RX 6000 in "early 2027". Tom's Hardware's report doesn't mention APUs or the Deck ([Tom's, 14 May 2026](https://www.tomshardware.com/pc-components/gpu-drivers/amd-makes-fsr-4-upscaling-official-for-radeon-rx-7000-and-6000-series-cards-rdna-3-and-rdna-2-chips-will-soon-enjoy-improved-visuals)).
  - The Deck appears only as [mezha's](https://mezha.ua/en/news/amd-fsr-4-rdna2-311296/amp/) own inference.
  - At Computex, AMD said RDNA2 needs extra work to reduce the shader cycles the upscaler uses, and gave no answer on integrated GPUs ([itc.ua, 16 Jun 2026](https://itc.ua/news/amd-nazvala-prychynu-zaderzhky-s-vnedrenyem-fsr-4-dlya-vydeokart-na-baze-rdna-2/)).
  - Handheld support this year is for RDNA3-class chips, and the Deck is not expected to get it ([Pocket Tactics, 8 Oct 2026](https://www.pockettactics.com/amd-fsr-4-gaming-handhelds)).
- **GE-Proton 11-3 OptiScaler integration: [checked].**
  - The release notes say "Added complete OptiScaler download, injection, and Protonfixes integration" ([GamingOnLinux, 25 Jul 2026](https://gamingonlinux.com/2026/07/ge-proton-11-3-brings-better-optiscaler-integration-amd-fsr4-improvements-and-lots-of-game-fixes)).
  - `PROTON_USE_OPTISCALER=1` appears only in a reader comment [could not verify].
  - This is GE-Proton, not Valve's default Proton, and it is still Tier I.
- **BC-250 FSR4 rc9 timings: [checked as reported].** 7.13 → 3.93 ms at 1080p ([Guru3D, 14 Sep 2026](https://www.guru3d.com/story/optimized-fsr-4-nearly-halves-upscaling-time-on-amd-repurposed-bc250-mining-board/)). The BC-250 is GFX1013, which has no accelerated dot product, so the Deck should do better per CU.
- **If official FSR4 reaches RDNA2:** reducing FSR4's shader cycles on RDNA2 is exactly D1's job, and AMD says it is doing that work.
  - If it costs 3 ms or less at 800p on the Deck, D1 has no niche.
  - If it costs ~5 ms like the leak, a model under 2 ms has a niche. That would be a generic model, not a per-game one.

## Verdicts

**D1 as specified: DEAD.**
- INT4 isn't available.
- The 15 ms anchor is wrong.
- The per-game evidence is misread.
- XeSS already sits at the same operating point.

**D1′ (rescue): SURVIVES WITH CHANGES.** Training is frozen until AMD's RDNA2 build ships. The changes:
- A generic temporal model for the Deck's budget: the whole chain at 2 ms or less at in-game clocks, INT8 only.
- Trained on engine content whose licence permits it, with full jitter control.
- Per-game adapters only if they buy at least 0.1 JOD.
- An immediate deliverable that needs no ML: per-game "XeSS at a lower internal resolution" profiles.

**D2 Low→High: DEAD** (the differences are non-local). Rescues tried: aligned pairs; a filter without motion vectors.

**D2′ (rescue): SURVIVES WITH CHANGES, as a 2-week test only.** The changes:
- A same-preset de-blur filter, fitted on the device.
- Beat a tuned CAS/RCAS, not untuned defaults.
- Use a native gamescope pass, or prove ReShade's overhead is 0.5 ms or less.
- My prior is that it ties CAS.

## Falsification experiments (bench OLED only, run by the bench runner and the owner)

**D1′: three gates.**
- **Gate 0, compute (days 1–5).**
  - A dev session writes a standalone Vulkan compute benchmark of the D1 network with random INT8 weights: 512×320 → 1280×800, including the kernel-apply and accumulate shaders, plus a 3×3 conv sweep at C = 8, 16, 32.
  - Run it at 15 W, with the GPU clock pinned to the median Wukong in-game clock from MangoHud.
  - Measure timestamp-query ms, achieved MAC/s ÷ peak, and check the ISA dump for `v_dot4_i32_i8`.
  - **Pass:** chain ≤ 2.0 ms. **Kill:** chain > 3.0 ms, or utilization under 15%.
- **Gate 1, baseline (days 3–10).**
  - Black Myth: Wukong Benchmark Tool with OptiScaler (the tool's anti-cheat status: could not verify).
  - Configs: FSR 3.1 at 640×400, XeSS at 640×400, XeSS at 512×320.
  - Frame time: median and p99 over 3 runs of 60 s each.
  - Quality: ColorVideoVDP with the Deck display model on 30 static views, after 64 frames of convergence, against a render-scale-200% reference. Plus a blind motion 2AFC test: a script randomizes the config, 3 viewers × 20 trials.
  - **Pass (thesis holds):** XeSS at 512×320 scores at least FSR at 640×400 minus 0.05 JOD, gets 50% or more preference, and its frame time is no higher than FSR's. If so, ship the XeSS profiles now.
  - **Kill:** XeSS at 512×320 loses by 0.2 JOD or more, *and* XeSS doesn't beat FSR at equal ms. A model would then have to be 40% cheaper than Intel's at equal quality, with per-game training buying 0.3 dB or less.
- **Gate 2, when AMD's RDNA2 FSR4 ships:** run the same harness. Kill D1′ if it costs 3 ms or less at 800p with quality at least equal to XeSS.
- **Owner by hand:**
  - install Decky Framegen / OptiScaler and the benchmark tool;
  - run the provided script;
  - sit the blind trials (about 1 h);
  - tape-measure his viewing distance.

**D2′.**
- **Days 1–4, pairs on the bench Deck:** 300 static views per game, for 3 games including Space Marine 2.
  - Input: deployed TAAU at Performance. Reference: the same preset at the game's maximum render scale.
  - Capture with lossless Steam screenshots. They exclude ReShade, which is what the inputs need.
- **Days 4–8, offline on a PC:**
  - Fit RAISR and a LUT network of about 100 KB on 200 views. Test on 100 held-out locations.
  - Baselines: the game's sharpening slider, CAS and RCAS, all tuned on the same 200 views.
  - Score ColorVideoVDP on stills and on a 10 s lossless motion clip per game.
- **Days 8–12, bench Deck:**
  - ReShade compute implementation.
  - Frame time with the effect on vs off, 3 × 60 s.
  - Latency: a 240 fps phone camera filming a button press until the screen reacts, 20 trials.
- **Pass:** at least +0.2 JOD over the best tuned sharpener in 2 of 3 games, video JOD no worse, cost ≤ 0.8 ms, p99 ≤ +1 ms, median latency ≤ +5 ms.
- **Kill:** under +0.1 JOD in all 3 games, *or* video JOD worse than CAS, *or* cost over 1.5 ms.
- **Owner by hand:** take the screenshot pairs from a checklist (about 3 h per game), run the toggle script, do the phone latency test.

## Verdict table

| Idea | Verdict |
|---|---|
| D1 (per-game DeckSR) | DEAD as specified → D1′ SURVIVES WITH CHANGES: generic Deck-budget INT8 model, gated, frozen until AMD's RDNA2 FSR4 ships; XeSS lower-res profiles now |
| D2 (Low→High filter in gamescope) | DEAD as specified → D2′ SURVIVES WITH CHANGES: same-preset de-blur, on-device fit, must beat tuned CAS; native pass or ≤0.5 ms ReShade overhead |

## What would change my mind

- **D1:** Gate 0 shows INT8 utilization of 35% or more *and* XeSS at a lower resolution beats FSR at equal ms. Or a published result where per-game training beats multi-game training by 1 dB or more on TAAU inputs.
- **D2:** a result on held-out locations of +0.2 JOD or more over a tuned CAS on TAAU output, from our test or from a paper.

**Key facts to keep:**
- ACO emits `v_dot4_i32_i8` on Van Gogh, but INT4 isn't reachable through Vulkan.
- XeSS DP4a on the Deck already uses dot4 through vkd3d-proton.
- gamescope's ReShade path runs on the general queue with a CPU wait.
- AMD has not committed FSR4 to the Deck. RDNA2 desktop cards get it in early 2027.
