# Neural reconstruction on 8 RDNA2 CUs: 6 ranked ideas (neural rendering / ML-systems view)

## The budget everything is measured against
- **Peak at 1.6 GHz (arithmetic from the brief's specs):** 8 CU × 64 lanes × 1.6 GHz = 0.82 T lane-cycles/s.
  - Packed FP16: 1.64 TMAC/s.
  - INT8 `v_dot4_i32_i8`: 3.28 TMAC/s (6.6 TOPS).
  - INT4 `v_dot8_i32_i4`: 6.55 TMAC/s (13.1 TOPS).
- **Verified:** gfx1033 uses `FeatureISAVersion10_3_0`, which includes `FeatureDot1Insts` (dot4/dot8) ([GCNProcessors.td](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Target/AMDGPU/GCNProcessors.td), [GCNFeatures.td](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Target/AMDGPU/GCNFeatures.td)). The per-lane rate matches Xbox Series X: 49/97 TOPS INT8/INT4 at 52 CU and 1.825 GHz, i.e. 8 and 16 ops per lane per clock ([PCGH](https://www.pcgameshardware.de/Xbox-Series-X-Konsolen-268616/Specials/Hardware-im-Detail-1345741/)).
- **Rule of thumb (est., 40% utilization):** 1 ms ≈ 1.3 GMAC INT8 ≈ 1,280 MAC per 800p output pixel ≈ 5,100 MAC per 640×400 input pixel. INT4 doubles that.
- **Anchors:**
  - **FSR2:** Performance mode at 1080p costs 0.5 ms on an RX 6650 XT (measured, [AMD README](https://github.com/GPUOpen-Effects/FidelityFX-FSR2)). Scaled to the Deck at 800p: ≈1.6 ms (est.).
  - **FSR4 INT8 on the Deck:** Spider-Man Ultra Performance drops from 90 to 70 fps vs FSR3, which is +3.2 ms ([steamdeckhq](https://steamdeckhq.com/news/we-can-now-use-fsr-4-on-the-steam-deck-for-better-visuals-with-a-power-tradeoff/), anecdotal). Another test saw about −10 fps in 3 games ([club386](https://www.club386.com/amd-fsr-4-now-works-on-steam-deck-thanks-to-modders-but-comes-at-a-cost/)). So FSR4 costs ≈4.5–5 ms total (est.).
  - **Arm NSS:** about 10 GOP per frame ([Arm](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/how-arm-neural-super-sampling-works)), which would take ≈3.8 ms on the Deck (est.).
- **At 800p the bottleneck is compute (ALU), not memory bandwidth.** A 3×3 16→16 INT8 conv does 72 MAC per byte; the Deck's balance point is 32 MAC per byte. This is unlike PSSR at 4K, where memory capped usable throughput at 18 of 300 TOPS ([Cerny via Gigazine](https://gigazine.net/gsc_news/en/20241219-playstation-5-pro-amd-technology)). On the Deck, MACs are what you spend.

---

## 1. Per-game-tuned parameter-prediction upscaler sized for 8 CUs ("DeckSR")
**Pitch:** an NSS-style network 3–4× smaller than FSR4, in INT8/INT4 with per-game adapters, so internal resolution can drop one notch (640×400 → 512×320) at FSR2-or-better quality.

- **Mechanism:**
  - Inputs come through OptiScaler's interception of the game's DLSS/FSR call: color, depth, motion vectors, jitter.
  - A 3-level UNet at input resolution (8/16/32 channels) predicts, per pixel: a 4×4 kernel, an accumulation weight (α), a history-rectification value (θ), and 4 hidden channels carried to the next frame. This is NSS's "parameter prediction" design; Arm found it quantizes well, while direct image prediction does not.
  - A classical shader applies the kernel and accumulates at 800p.
  - The generic base model is distilled once. Each game gets a small adapter (per-channel scale and shift, about 1–4 KB).
  - Loss: ColorVideoVDP configured for a 7.4" screen, 1280 px wide, at 35 cm, plus a flicker term.
- **Why it could beat the wall:**
  - Fitting a small model to one game's content lets it match a larger generic one. In NAS, per-video models consistently improved quality, while a generic model sometimes made it worse ([NAS, OSDI'18](https://www.usenix.org/conference/osdi18/presentation/yeo)).
  - dot4/dot8 give 2–4× the FP16 rate, and FSR2's hand-written heuristics never use them.
- **Budget math:**
  - Encoder: 256K px × 1.0K MAC + 64K × 5K + 16K × 20K ≈ 0.9 GMAC. The decoder is about the same, so ≈1.5 GMAC total.
  - Network time: 1.15 ms in INT8, ~0.8 ms with INT4 middle layers.
  - Pre/post shaders ≈1.0 ms (16-tap kernel at 800p is 16M fetches, ≈0.3 ms at 51 GT/s, plus reprojection).
  - **Total ≈2.0–2.4 ms**, vs FSR2 at 1.6 ms and FSR4 INT8 at ~4.7 ms (all est.).
  - Payoff: if pixel-proportional work at 640×400 is 15 ms (est.), 512×320 saves 36% of it (5.4 ms). Net gain ≈4.5 ms, e.g. 33 → 28.5 ms. Memory under 20 MB.
- **Tools:** OptiScaler, `VK_KHR_shader_integer_dot_product` (core in Vulkan 1.3), PyTorch quantization-aware training, [ColorVideoVDP](https://arxiv.org/abs/2401.11485), which is differentiable and takes display geometry as input.
- **Prior art:** NSS (4 ms target, quantization-aware training); FSR4 INT8 on the Deck (works, about 10 fps cost). DLSS 1.0 was trained per game and was dropped for the generic, temporal DLSS 2 ([NVIDIA](https://www.nvidia.com/en-us/geforce/news/nvidia-dlss-2-0-a-big-leap-in-ai-rendering/)). The lesson: per-game training should only be an adapter on top of a temporal backbone, not the whole model.
- **Tier I.** Games without anti-cheat that expose upscaler inputs (e.g. Wukong, Alan Wake 2, Stalker 2).
- **Cheapest falsification (2 weeks):**
  - On a PC, capture ~5k frames of upscaler inputs plus references built by accumulating 64 jittered samples per pixel in photo mode.
  - Train the student network.
  - Measure ColorVideoVDP (JOD) on held-out areas: student at 512×320 vs FSR2 at 640×400.
  - Time the shader chain on recorded inputs on the bench Deck using timestamp queries.
  - **Kill if** the gain is under +0.25 JOD, or the chain takes over 2.5 ms.
- **Biggest risk:** tiny networks fail exactly at disocclusions, transparencies and particles.

## 2. Neural refinement of the history buffer, run in async-compute gaps
**Pitch:** move the heavy network off the critical path. It refines last frame's 800p accumulated history, 1/4 of the tiles per frame, while the GPU is busy with shadow and depth passes that are limited by the rasterizer, not the ALUs.

- **Mechanism:**
  - A cheap accumulator runs every frame (FSR2-class or idea #1).
  - A larger refiner (~6 GMAC for a full frame, FSR4-class) reads history from frame N−1 plus the disocclusion/rejection masks, and rewrites corrected tiles. The history is then reprojected forward like any TAA history.
  - Tile scheduling: round-robin, with priority for tiles whose history was rejected.
  - It needs no frame-N data, so the Vulkan layer submits it on its own compute queue (added at `vkCreateDevice`) at the start of frame N, overlapping the shadow and depth passes.
- **Why it could beat the wall:** TAA history changes slowly, so a correction stays valid for several frames. NEMO ran super-resolution only on selected anchor frames: 11.5× throughput and −88.6% energy on Android ([NEMO](https://ina.kaist.ac.kr/projects/nemo/)). Rasterizer-bound passes leave ALUs idle.
- **Budget math:** 6 GMAC ÷ 4 = 1.5 GMAC per frame ≈ 1.15 ms. If about half hides in the idle gaps, ~0.6 ms is visible (est.). Memory traffic ≈4 MB per frame.
- **Tools:** Radeon GPU Profiler captures through RADV (`MESA_VK_TRACE=rgp`) to find the gaps.
- **Prior art:** NEMO; [reverse reprojection caching (Nehab 2007)](https://diglib.eg.org/handle/10.2312/EGGH.EGGH07.025-036); the temporal reuse in Lumen and ReSTIR.
- **Tier I**, same games as #1.
- **Cheapest falsification:**
  - Offline: on recorded sequences, compare refining every frame against refining 1/2, 1/4 and 1/8 of tiles per frame, across pan speeds, scored with ColorVideoVDP.
  - On the Deck: one RGP capture, adding up idle ALU time during the shadow and depth passes.
  - **Kill if** refining 1/4 of tiles keeps under 50% of the every-frame gain, or the idle gap is under 1 ms per frame.
- **Biggest risk:** errors cluster in the newest history (disocclusions), which is exactly where the refinement arrives late.

## 3. Learned restoration in the compositor, run on the texture units
**Pitch:** replace gamescope's FSR1/NIS with a per-game learned filter bank ([RAISR](https://arxiv.org/abs/1606.01299)) or a ~100 KB lookup-table network ([HKLUT](https://arxiv.org/abs/2312.06101)), trained by least squares on the Deck itself. This is the only neural option for anti-cheat games.

- **Mechanism:**
  - The game uses its own TAAU/FSR2 at Performance, which is a game setting (Tier S), and outputs 800p.
  - gamescope then applies a per-game filter. RAISR version: sort each pixel into one of 216 buckets by gradient angle, strength and coherence, then apply that bucket's 11×11 luma filter. HKLUT version: a trained CNN baked into lookup tables that the texture units sample.
  - Training pairs: the deployed settings vs the High preset on the same static views (photo mode, pause screens, or the free MH Wilds and Wukong benchmark tools).
  - RAISR training is linear least squares per bucket and takes minutes on the Zen 2. Nothing derived from game assets leaves the device.
- **Why it could beat the wall:**
  - It moves the "neural" work from the weak ALUs to the texture units and L2. A 100 KB table fits in the 1 MB L2.
  - The degradation it learns to undo is fixed and learnable: that game's upscaler at that ratio.
- **Budget math:** RAISR is 121 MAC/px × 1.02M px = 0.12 GMAC FP16 ≈ 0.2 ms, plus ~0.1–0.2 ms for bucketing, so **~0.3–0.5 ms** (est.). RAISR already exceeded 200 Mpix/s on a 2016 mobile GPU. It must be a native gamescope pass on gamescope's async queue: gamescope's ReShade path runs on the general queue and adds latency ([GamingOnLinux](https://gamingonlinux.com/2023/09/gamescope-added-support-for-reshade-shaders-on-linux-steamos)).
- **Prior art:** RAISR. On Set5 at ×4, SR-LUT scores 29.82 dB and HKLUT 30.35 dB, vs bicubic at 28.42 (measured, in the HKLUT paper). gamescope's existing FSR1/NIS filters.
- **Tier S.** All games, including Space Marine 2 and Helldivers 2.
- **Cheapest falsification:** collect 300 paired stills per game, fit offline, and measure FLIP and ColorVideoVDP on held-out frames against FSR1 + RCAS sharpening and against the bare TAAU output. Add a flicker check on a 10 s recording. **Kill if** the gain over RCAS is under +0.2 JOD.
- **Biggest risk:** with no motion vectors it may sharpen the TAA shimmer, and the gain may be indistinguishable from simply sharpening well.

## 4. Camera-rotation warp in gamescope, driven by the latest stick/gyro input
**Pitch:** on display refreshes the game misses, rotate the last frame to where the camera will be, predicted from stick or gyro input by a small per-game model. This adds presented frames and cuts latency, so track it separately from native fps.

- **Mechanism:**
  - Read the controller and gyro read-only in parallel with Steam (hidraw).
  - A ~10K-parameter per-game model (GRU) maps recent input to camera angular velocity. It is learned from gameplay recordings by fitting the global rotation of distant scenery against the input log.
  - A pure rotation warp is the same at every depth, so no depth buffer is needed.
  - Learned per-game masks keep the HUD and first-person weapon fixed on screen.
  - Confidence gate: if the last real frame's rotation disagrees with the prediction (menus, cutscenes, lock-on), stop warping.
- **Why it could beat the wall:** for camera rotation, most of what you see in a pan, the pixels already exist. Latency for look input drops from the game's pipeline depth to one refresh.
- **Budget math:**
  - Cost: one bilinear tap per pixel inside the existing composite pass, ≈0.05–0.1 ms. The predictor takes microseconds on the CPU.
  - Exposed screen edge: at 180°/s and 90 Hz, about 2° of an ~85° horizontal field of view ≈ 30 px; fill by clamping or blurring.
  - Rotation latency ≈50–60 ms → ≈15–20 ms (est.).
  - For comparison, NVIDIA's Reflex 2 Frame Warp measured 27 → 14 ms ([NVIDIA](https://www.nvidia.com/en-us/geforce/news/reflex-2-even-lower-latency-gameplay-with-frame-warp)).
- **Prior art:** VR async reprojection ([Google](https://developers.google.com/vr/discover/async-reprojection)); Reflex 2 Frame Warp. Learned frame extrapolation is far too heavy here: PatchEX needs 0.7–2 ms of inference on an RTX 4080 ([PatchEX](https://arxiv.org/abs/2407.17501); see also [GFFE](https://www.intel.com/content/www/us/en/developer/articles/technical/gffe-g-buffer-free-frame-extrapolation.html)). So warp, not a network.
- **Tier S.** Best for first-person games.
- **Cheapest falsification:** record Stalker 2 with an input log and fit the predictor. At an 11 ms horizon, compare FLIP(warped frame, true next frame) against FLIP(repeated frame, true next frame). **Kill if** the warp wins on under 80% of pan frames.
- **Biggest risk:** third-person orbit cameras (MH Wilds, Wukong, Alan Wake 2, Space Marine 2) make the character slide. These need per-game separation of the character from the background, or the warp is disabled.

## 5. Learned pass skipping: predict an expensive pass instead of computing it
**Pitch:** run the single most expensive screen-space pass (global-illumination gather, volumetric fog, or screen-space reflections) every other frame. On the skipped frames, reproject its previous output and correct it with a tiny network.

- **Mechanism:** identify the pass by its pipeline hash from an RGP capture. The Vulkan layer skips its dispatch on odd frames and writes the reprojected previous output plus a correction. The correction's inputs are the reprojected result, depth, motion vectors and the disocclusion mask.
- **Budget math:** for a pass costing X ms, saving = X/2 minus the correction (≈0.3 GMAC FP16 ≈ 0.4 ms). For X = 4 ms, that is 1.6 ms saved (est.).
- **Prior art:** reprojection caching; PS4 Pro checkerboard rendering; NNAO and Deep Shading (learned screen-space passes).
- **Tier I.**
- **Cheapest falsification:** RGP per-pass timings on the Deck for one UE5 game at target settings. **Kill if** no skippable pass costs at least 2 ms, or if UE5 config variables (Tier S) already get within 0.5 ms.
- **Biggest risk:** fragile per-game reverse engineering (patches change the hashes), and passes that feed other temporal filters, which doubles the ghosting.

## 6. CPU as a neural coprocessor: only for small control models
- **The math:**
  - Zen 2 runs `VPMADDUBSW ymm` at 1 per clock on one port ([uops.info](https://uops.info/html-instr/VPMADDUBSW_YMM_YMM_YMM.html)): at most 32 INT8 MAC per clock per core, ~16 after widening.
  - Two spare cores at 3 GHz give ≈0.1–0.2 TMAC/s, which is 3–6% of the GPU's INT8 rate.
  - Those cores also cost ~1–2 W each (est.) out of the same 15 W budget.
- **Verdict:** per-pixel inference on the CPU is a net loss. Use it for:
  - the input-to-camera predictor in #4;
  - a predictor of next-frame GPU time that adjusts the fps cap and the CPU/GPU power split ahead of spikes, to help 1% lows.
- **Tier S.**
- **Cheapest falsification:** run a 640×400 INT8 conv on 2 cores while the GPU is loaded, and measure the GPU clock drop against the work done.

---

## Unknown unknowns
1. **Benchmarks from other boards don't transfer.** The BC-250 mining board, the source of the community's FSR4 INT8 timings (3.93 ms at 1080p, measured, [Guru3D](https://www.guru3d.com/story/optimized-fsr-4-nearly-halves-upscaling-time-on-amd-repurposed-bc250-mining-board/)), is gfx1013 and has no dot4 instructions, while gfx1033 does (LLVM, links above). Still to check: that ACO actually emits `v_dot4` for SPIR-V `OpSDotKHR` (`RADV_DEBUG=shaders`), and that the OLED reports gfx1033. I could not fetch Mesa's source to confirm the first point.
2. **Watts matter more than FLOPS.** The 15 W budget is shared, and under game load the GPU often runs below 1.6 GHz. Measure operations per joule with the GPU busy, not peak rates.
3. **Pixels per degree.** 1280 px across 159 mm is 0.124 mm/px: 42 px/degree at 30 cm, 56 at 40 cm. The assumed viewing distance decides which artifacts are visible, so measure real handheld distance before tuning ColorVideoVDP. On OLED, banding from INT8 output quantization shows near black, so predict filter parameters, not colors.
4. **Texture mip bias.** Below the game's expected internal resolution, the texture LOD bias must follow (OptiScaler can override it), or no network can recover texture detail. Training data must use the same bias.
5. **Legal lines.**
   - The FSR4 INT8 build in circulation comes from an accidental AMD GitHub push ([igor'sLAB](https://www.igorslab.de/en/amd-fsr-4-leak-how-a-botched-github-push-reshuffles-the-cards/)). Don't ship it, and don't distill a model from it.
   - Models fitted to a single game can memorize its textures, which could amount to redistributing assets. Train on the user's device, or cap model size and test for memorization.

**Other sources:** [TechSpot's FSR4 INT8 tests on RDNA2/3](https://www.techspot.com/article/3040-amd-fsr4-upscaling-older-radeon-gpu/) (needs about two quality modes lower to match FSR3's speed).

**Considered and rejected:**
- **Neural texture compression:** it needs a small network evaluated at every texture sample, and the Deck has no matrix cores. Decoding to standard compressed textures at load time only saves disk space.
- **Neural radiance caching:** it trains a network online every frame, which is too expensive at this budget.
